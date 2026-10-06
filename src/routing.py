"""
Adaptive Multi-Criteria Routing Module
Implements Formulas (12)–(18), link cost metric W(i,j), Dijkstra path selection,
and the Fig. 4 flow offloading / load balancing algorithm.
Reference: Beshley et al., JCN 2024, Section V.
"""

from typing import Dict, Any, List, Tuple
import networkx as nx
import numpy as np

class MultiCriteriaRouter:
    """
    Computes optimal paths in the SOSDN topology based on normalized QoS criteria
    and adaptive criterion weighting.
    """
    def __init__(self, config: Dict[str, Any], topology):
        self.config = config
        self.topology = topology
        self.routing_cfg = config['routing']

    def compute_link_metrics(self, weights: np.ndarray) -> Dict[Tuple[str, str], float]:
        """
        Calculates W(i,j) for every directed link in the network using Formula (16):
        W_ij = 1 - (X1 * P_ij + X2 * D_ij + X3 * C_ij + X4 * J_ij)
        """
        graph = self.topology.graph

        # 1. Collect all edge measurements to find normalizing extrema
        losses = [d['packet_loss_percent'] for _, _, d in graph.edges(data=True)]
        delays = [d['delay_ms'] for _, _, d in graph.edges(data=True)]
        jitters = [d['jitter_ms'] for _, _, d in graph.edges(data=True)]
        bws = [d['available_bw_mbps'] for _, _, d in graph.edges(data=True)]

        p_min = max(0.01, min(losses))
        t_min = max(0.5, min(delays))
        j_min = max(0.2, min(jitters))
        b_max = max(1.0, max(bws))

        link_weights = {}

        for u, v, d in graph.edges(data=True):
            # Formula (12) / Normalized loss: P_min / P_ij
            p_val = max(0.01, d['packet_loss_percent'])
            P_norm = min(1.0, p_min / p_val)

            # Formula (13) / Normalized delay: t_min / t_ij
            t_val = max(0.5, d['delay_ms'])
            D_norm = min(1.0, t_min / t_val)

            # Formula (14) / Normalized bandwidth: B_ij / B_max
            b_val = max(0.1, d['available_bw_mbps'])
            C_norm = min(1.0, b_val / b_max)

            # Formula (15) / Normalized jitter: jt_min / jt_ij
            j_val = max(0.2, d['jitter_ms'])
            J_norm = min(1.0, j_min / j_val)

            # Formula (16)
            W_ij = 1.0 - (
                weights[0] * P_norm +
                weights[1] * D_norm +
                weights[2] * C_norm +
                weights[3] * J_norm
            )
            
            # Metric cost must be non-negative for shortest path routing
            link_weights[(u, v)] = max(0.001, float(W_ij))

        return link_weights

    def get_category_weights(self, category: int) -> np.ndarray:
        """Retrieves adaptive criterion weights [X1, X2, X3, X4] tailored for flow category."""
        ad_cfg = self.routing_cfg['adaptive_weights_by_category']
        if category == 1:
            w_dict = ad_cfg['category_1']
        elif category == 2:
            w_dict = ad_cfg['category_2']
        else:
            w_dict = ad_cfg['category_3']

        weights = np.array([w_dict['loss'], w_dict['delay'], w_dict['bandwidth'], w_dict['jitter']], dtype=float)
        # Verify Formula (18): sum(X_k) == 1
        weights = weights / np.sum(weights)
        return weights

    def find_ospf_path(self, src: str, dst: str) -> List[str]:
        """
        Baseline OSPF: finds shortest path based on static hop counts / base link delays.
        Ignores dynamic multi-criteria congestion.
        """
        return nx.shortest_path(self.topology.graph, source=src, target=dst, weight='base_delay_ms')

    def find_multicriteria_path(self, src: str, dst: str, category: int) -> Tuple[List[str], float]:
        """
        Proposed Method: calculates link costs W_ij and finds path minimizing F(path) = sum(W_ij).
        """
        weights = self.get_category_weights(category)
        link_costs = self.compute_link_metrics(weights)

        # Build weighted temporary graph
        temp_g = nx.DiGraph()
        for (u, v), cost in link_costs.items():
            temp_g.add_edge(u, v, weight=cost)

        path = nx.shortest_path(temp_g, source=src, target=dst, weight='weight')
        path_cost = sum(link_costs[(path[i], path[i+1])] for i in range(len(path)-1))
        return path, path_cost

    def execute_congestion_offloading(self, active_flows: List[Any], threshold_pct: float = 85.0):
        """
        Implements Fig. 4 (Load balancing algorithm):
        1. Identifies overloaded switches/ports where utilization > threshold.
        2. Inspects flows traversing the congested link.
        3. Re-routes flows in ascending priority order (Category 3 first, then Category 2).
        4. Category 1 flows are protected from splitting/redirection.
        """
        graph = self.topology.graph
        
        # Check all core links
        for u, v, d in graph.edges(data=True):
            utilization = (d['current_load_mbps'] / d['capacity_mbps']) * 100.0
            if utilization > threshold_pct:
                # Find traversing flows
                traversing_flows = [
                    f for f in active_flows
                    if len(f.active_path) > 1 and any(
                        f.active_path[i] == u and f.active_path[i+1] == v
                        for i in range(len(f.active_path)-1)
                    )
                ]

                # Sort flows by ascending category/priority (Category 3 first)
                traversing_flows.sort(key=lambda x: (x.assigned_category != 3, x.relative_priority))

                for flow in traversing_flows:
                    if flow.assigned_category == 3:
                        # Find alternative detour path avoiding the congested link (u, v)
                        alt_graph = graph.copy()
                        if alt_graph.has_edge(u, v):
                            alt_graph.remove_edge(u, v)
                        try:
                            alt_path = nx.shortest_path(alt_graph, source=flow.source_switch, target=flow.destination_switch, weight='base_delay_ms')
                            # Migrate flow
                            flow.active_path = alt_path
                            d['current_load_mbps'] -= flow.bandwidth_mbps
                            # If offloaded below threshold, break
                            if (d['current_load_mbps'] / d['capacity_mbps']) * 100.0 <= threshold_pct:
                                break
                        except nx.NetworkXNoPath:
                            continue
