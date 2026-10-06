"""
Baseline & Method Controller Module
Orchestrates the 4 comparison methods:
1. FIFO + OSPF
2. PQ + OSPF
3. Adaptive Prioritization + OSPF
4. Proposed Combined (SOSDN)
Reference: Beshley et al., JCN 2024, Section VII, Fig. 10 & Fig. 11.
"""

from typing import Dict, Any, List
import numpy as np

class MethodOrchestrator:
    """Manages routing, prioritization, and server selection for a specified experimental method."""
    def __init__(
        self,
        method_cfg: Dict[str, Any],
        topology,
        router,
        prioritizer,
        server_selector,
        monitor
    ):
        self.method_id = method_cfg['id']
        self.method_name = method_cfg['name']
        self.routing_type = method_cfg['routing']  # 'ospf' or 'multi_criteria'
        self.queue_type = method_cfg['queue']      # 'fifo', 'pq', 'adaptive_pq'
        self.use_adaptive_priority = method_cfg['adaptive_priority']
        self.server_selection_type = method_cfg['server_selection'] # 'static' or 'optimal'
        
        self.topology = topology
        self.router = router
        self.prioritizer = prioritizer
        self.server_selector = server_selector
        self.monitor = monitor

    def execute_method(
        self,
        flows: List[Any],
        scenario_name: str,
        seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Executes traffic engineering for all active flows under this method.
        Returns per-flow execution telemetry.
        """
        # 1. Update initial network metrics so router sees current link background load
        self.monitor.update_network_metrics(seed=seed)

        # 2. Server Selection for each flow
        server_request_counts = {}
        for f in flows:
            server_id = self.server_selector.select_server(
                service_type=f.target_service,
                method=self.server_selection_type
            )
            f.selected_server_id = server_id
            f.destination_switch = self.topology.get_server_location(server_id)
            server_request_counts[server_id] = server_request_counts.get(server_id, 0) + 1

        # 3. Update server load metrics based on server selection
        self.monitor.update_server_metrics(server_request_counts, seed=seed)

        # 4. Service Prioritization
        if self.use_adaptive_priority:
            # Under adaptive prioritization, when high congestion is present,
            # User 7 (strict SLA IPTV user experiencing degradation) receives SLA boost
            degraded_id = 7 if scenario_name == 'high_congestion' else None
            self.prioritizer.assign_flow_priorities(flows, degraded_user_id=degraded_id)
        else:
            # Baseline static priorities
            for f in flows:
                f.relative_priority = 0.5
                if self.queue_type == 'fifo':
                    f.assigned_category = 3
                    f.dscp_code = "000000"
                else:  # Static PQ (RFC-based: Voice=1, Video=2, Data=3)
                    if f.service_class == 'A':
                        f.assigned_category = 1
                        f.dscp_code = "001100"
                    elif f.service_class == 'C':
                        f.assigned_category = 2
                        f.dscp_code = "001010"
                    else:
                        f.assigned_category = 3
                        f.dscp_code = "001001"

        # 5. Route Selection
        flow_path_costs = {}
        for f in flows:
            if self.routing_type == 'ospf':
                path = self.router.find_ospf_path(f.source_switch, f.destination_switch)
                f.active_path = path
                flow_path_costs[f.flow_id] = len(path) * 0.1  # nominal hop cost
            else:
                # Multi-criteria routing using W(i,j)
                path, cost = self.router.find_multicriteria_path(
                    f.source_switch,
                    f.destination_switch,
                    category=f.assigned_category
                )
                f.active_path = path
                flow_path_costs[f.flow_id] = cost

            # Allocate flow bandwidth along path
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                self.topology.graph[u][v]['current_load_mbps'] += f.bandwidth_mbps

        # 6. Apply Congestion Offloading if proposed multi-criteria method
        if self.routing_type == 'multi_criteria':
            self.router.execute_congestion_offloading(flows, threshold_pct=82.0)

        # 7. Update link QoS metrics with full allocated load
        self.monitor.update_network_metrics(seed=seed)

        # 8. Collect final metrics per flow
        results = []
        for f in flows:
            path = f.active_path
            e2e_net_loss, net_delay, net_jitter, avail_bw = self.monitor.get_path_metrics(path)
            
            # Incorporate server delay and server drop
            srv = self.topology.server_nodes[f.selected_server_id]
            srv_delay = srv['proc_time_ms']
            srv_loss = srv['loss_prob']

            # Adjust network delay, loss, and jitter by queuing discipline
            if self.queue_type == 'fifo':
                # FIFO treats all packets equally; all share bottleneck queuing
                flow_net_delay = net_delay
                flow_net_loss = e2e_net_loss
                flow_jitter = net_jitter
            elif self.queue_type == 'pq':
                # Static PQ: Class A (Cat 1) gets high priority; Class C (Cat 2) gets normal video priority
                if f.assigned_category == 1:
                    flow_net_delay = net_delay * 0.40
                    flow_net_loss = e2e_net_loss * 0.30
                    flow_jitter = net_jitter * 0.40
                elif f.assigned_category == 2:
                    flow_net_delay = net_delay * 0.75
                    flow_net_loss = e2e_net_loss * 0.70
                    flow_jitter = net_jitter * 0.75
                else:
                    flow_net_delay = net_delay * 1.25
                    flow_net_loss = e2e_net_loss * 1.30
                    flow_jitter = net_jitter * 1.20
            else:  # 'adaptive_pq'
                # Adaptive PQ: Elevated flows (e.g. User 7 boosted to Cat 1) receive strict highest priority
                if f.assigned_category == 1:
                    flow_net_delay = net_delay * 0.30
                    flow_net_loss = e2e_net_loss * 0.20
                    flow_jitter = net_jitter * 0.30
                elif f.assigned_category == 2:
                    flow_net_delay = net_delay * 0.65
                    flow_net_loss = e2e_net_loss * 0.55
                    flow_jitter = net_jitter * 0.65
                else:
                    flow_net_delay = net_delay * 1.25
                    flow_net_loss = e2e_net_loss * 1.30
                    flow_jitter = net_jitter * 1.20

            # Total end-to-end delay (Formula 2: Network + Server)
            total_delay = flow_net_delay + srv_delay
            # Total packet loss
            total_loss = min(100.0, flow_net_loss + srv_loss)
            total_jitter = flow_jitter

            cost = flow_path_costs.get(f.flow_id, 0.25)

            results.append({
                'flow_id': f.flow_id,
                'user_id': f.user_id,
                'service_type': f.service_type,
                'service_class': f.service_class,
                'category': f.assigned_category,
                'priority': f.relative_priority,
                'selected_server': f.selected_server_id,
                'path_str': "->".join(f.active_path),
                'path_hops': len(f.active_path),
                'path_cost': cost,
                'loss_percent': float(total_loss),
                'delay_ms': float(total_delay),
                'jitter_ms': float(total_jitter),
                'available_bw_mbps': float(avail_bw),
                'server_cpu': float(srv['cpu_load']),
                'server_ram': float(srv['ram_load'])
            })

        return results
