"""
Optimal Service Server Selection Module
Implements Formula (19) and Table III for multi-criteria server selection.
Reference: Beshley et al., JCN 2024, Section VI, Fig. 8.
"""

from typing import Dict, Any, List
import numpy as np

class ServerSelector:
    """
    Selects the optimal service server among eligible candidates
    using the normalized integral additive criterion.
    """
    def __init__(self, config: Dict[str, Any], topology):
        self.config = config
        self.topology = topology
        self.weights_cfg = config['server_selection']['criteria_weights']
        
        # Alpha weights: [CPU, RAM, ProcTime, LossProb, NIC] = [0.3, 0.2, 0.2, 0.2, 0.1]
        self.alpha = np.array([
            self.weights_cfg['cpu'],
            self.weights_cfg['ram'],
            self.weights_cfg['proc_time'],
            self.weights_cfg['loss_prob'],
            self.weights_cfg['nic_load']
        ], dtype=float)

    def get_candidate_servers(self, service_type: str) -> List[Dict[str, Any]]:
        """Returns all registered server instances capable of serving this service type."""
        candidates = []
        for s_id, s_data in self.topology.server_nodes.items():
            if s_data['type'] == service_type or (service_type in ["IPTV", "VOD"] and s_data['type'] == "REPLICATED"):
                candidates.append(s_data)
        return candidates

    def compute_server_utility(self, candidate_servers: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Implements Formula (19):
        F(x) = sum_{i=1}^5 alpha_i * (f_i^0 / f_i(x)) -> max
        Where f_i^0 is the minimum (best) value across all candidate servers.
        """
        if not candidate_servers:
            return {}

        # 1. Collect criterion vectors for each candidate
        # Vector format: [cpu_load, ram_load, proc_time_ms, loss_prob, nic_load]
        server_vectors = {}
        for s in candidate_servers:
            vec = np.array([
                max(1.0, s['cpu_load']),
                max(1.0, s['ram_load']),
                max(1.0, s['proc_time_ms']),
                max(0.01, s['loss_prob']),
                max(1.0, s['nic_load'])
            ], dtype=float)
            server_vectors[s['id']] = vec

        # 2. Determine best minimum divisors f_i^0 across candidates
        all_vecs = np.array(list(server_vectors.values()))
        f_0 = np.min(all_vecs, axis=0)

        # 3. Calculate generalized additive criterion F(x)
        utilities = {}
        for s_id, vec in server_vectors.items():
            # Normalized components f_i^0 / f_i
            normalized_terms = f_0 / vec
            utility = float(np.sum(self.alpha * normalized_terms))
            utilities[s_id] = utility

        return utilities

    def select_server(self, service_type: str, method: str = "optimal") -> str:
        """
        Selects server based on experimental method:
        - "static": default fixed assignment (e.g. Server 2 for IPTV, which is heavily loaded)
        - "optimal": applies Formula (19) to find max utility server
        """
        candidates = self.get_candidate_servers(service_type)
        if not candidates:
            # Fallback to any server
            return list(self.topology.server_nodes.keys())[0]

        if method == "static":
            # Baseline uses default or round-robin without load consideration
            if service_type == "IPTV":
                # In baseline, requests default to IPTV_Server_2 (the heavily loaded server described in Section VII)
                return "IPTV_Server_2"
            return candidates[0]['id']

        # Proposed optimal selection: max F(x)
        utilities = self.compute_server_utility(candidates)
        best_server = max(utilities.items(), key=lambda item: item[1])[0]
        return best_server
