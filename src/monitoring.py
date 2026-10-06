"""
Network & Server Monitoring Module for SOSDN Simulation
Emulates the SDN Controller monitoring system (sFlow & OpenFlow counters).
Reference: Beshley et al., JCN 2024, Section III, Section V, Section VII.
"""

from typing import Dict, Any, List, Tuple
import numpy as np

class SOSDNMonitor:
    """Monitors link-level and server-level performance metrics in real-time."""
    def __init__(self, config: Dict[str, Any], topology):
        self.config = config
        self.topology = topology

    def update_network_metrics(self, seed: int = 42):
        """
        Calculates dynamic link metrics (loss, delay, jitter, available bandwidth)
        based on current traffic loads using M/M/1/B queuing models.
        """
        np.random.seed(seed)
        graph = self.topology.graph

        for u, v, d in graph.edges(data=True):
            capacity = d['capacity_mbps']
            load = d['current_load_mbps']
            base_delay = d['base_delay_ms']

            # Utilization ratio rho = lambda / C
            rho = load / capacity

            if rho < 0.70:
                # Underloaded: minimal queuing, negligible drops
                queue_delay = (rho / (1.0 - rho + 0.1)) * 1.5
                loss = max(0.01, (rho ** 4) * 0.15)
                jitter = max(0.5, queue_delay * 0.20 + np.random.uniform(0.1, 0.4))
            elif rho < 0.90:
                # Moderately loaded: noticeable queuing, slight loss
                queue_delay = 5.0 + ((rho - 0.70) / 0.20) * 15.0
                loss = 0.10 + ((rho - 0.70) / 0.20) * 0.40
                jitter = 2.0 + ((rho - 0.70) / 0.20) * 10.0
            elif rho < 0.98:
                # Heavily congested: steep queuing delay, substantial drop
                queue_delay = 20.0 + ((rho - 0.90) / 0.08) * 45.0
                loss = 0.50 + ((rho - 0.90) / 0.08) * 0.60  # up to 1.1%
                jitter = 12.0 + ((rho - 0.90) / 0.08) * 25.0
            else:
                # Severe bottleneck / buffer saturation
                queue_delay = 65.0 + min(30.0, (rho - 0.98) * 100.0)
                loss = min(1.8, 1.1 + (rho - 0.98) * 10.0)
                jitter = min(45.0, 37.0 + (rho - 0.98) * 50.0)

            total_delay = base_delay + queue_delay
            available_bw = max(0.1, capacity - load)

            d['delay_ms'] = total_delay
            d['packet_loss_percent'] = loss
            d['jitter_ms'] = jitter
            d['available_bw_mbps'] = available_bw

    def update_server_metrics(self, server_request_counts: Dict[str, int], seed: int = 42):
        """
        Dynamically adjusts server load metrics (CPU, RAM, proc time, drop prob, NIC)
        based on allocated request volumes.
        """
        np.random.seed(seed)
        for sid, s_data in self.topology.server_nodes.items():
            reqs = server_request_counts.get(sid, 0)
            s_data['active_requests'] = reqs

            scale = 1.0 + (reqs * 0.02)
            cfg_server = next(s for s in self.config['servers']['instances'] if s['id'] == sid)
            
            s_data['cpu_load'] = min(95.0, cfg_server['base_cpu_load'] * scale + np.random.uniform(-1.0, 1.0))
            s_data['ram_load'] = min(90.0, cfg_server['base_ram_load'] * (1.0 + reqs * 0.015) + np.random.uniform(-0.5, 0.5))
            
            # Processing time: Server 1 ~100ms, Server 2 ~180ms under nominal load
            load_factor = (s_data['cpu_load'] / 100.0)
            s_data['proc_time_ms'] = cfg_server['base_proc_time_ms'] * (0.8 + 0.4 * load_factor)
            s_data['loss_prob'] = cfg_server['base_loss_prob'] * (0.8 + 0.3 * load_factor)
            s_data['nic_load'] = min(95.0, cfg_server['base_nic_load'] * scale)

    def get_path_metrics(self, path: List[str]) -> Tuple[float, float, float, float]:
        """Aggregates end-to-end network metrics across hops in a path."""
        graph = self.topology.graph
        if len(path) < 2:
            return 0.0, 0.0, 0.0, 100.0

        total_delay = 0.0
        success_prob = 1.0
        jitter_sq_sum = 0.0
        min_bw = float('inf')

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            d = graph[u][v]
            total_delay += d['delay_ms']
            success_prob *= (1.0 - (d['packet_loss_percent'] / 100.0))
            jitter_sq_sum += (d['jitter_ms'] ** 2)
            min_bw = min(min_bw, d['available_bw_mbps'])

        e2e_loss = (1.0 - success_prob) * 100.0
        e2e_jitter = np.sqrt(jitter_sq_sum)

        return e2e_loss, total_delay, e2e_jitter, min_bw
