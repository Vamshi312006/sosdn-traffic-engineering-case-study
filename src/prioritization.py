"""
Adaptive Service Prioritization Module
Implements Formulas (5)–(9) and classification into 3 categories.
Reference: Beshley et al., JCN 2024, Section IV, Tables I & II, Fig. 3 & Fig. 4.
"""

from typing import Dict, Any, List
import numpy as np

class AdaptivePrioritization:
    """
    Computes dynamic flow priorities using multi-parameter QoS requirements,
    service importance, and SLA policies.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classes_cfg = config['services']['classes']
        self.z_weights = config['prioritization']['parameter_weights']
        
        # Z vector: [loss, delay, jitter, bandwidth] = [0.23, 0.18, 0.14, 0.12]
        self.Z = np.array([
            self.z_weights['loss'],
            self.z_weights['delay'],
            self.z_weights['jitter'],
            self.z_weights['bandwidth']
        ], dtype=float)

        # Baseline reference minimums from Table I
        self.P_min = 0.1    # min loss % across classes (Class D/E = 0.1%)
        self.T_min = 100.0  # min delay ms (Class B/C/D = 100 ms)
        self.J_min = 10.0   # min jitter ms (Class A = 10 ms)
        self.C_max = 10000.0 # max bandwidth kbps (Class F = 10000 kbps)

    def calculate_relative_qos_vector(self, loss_pct: float, delay_ms: float, jitter_ms: float, bw_kbps: float) -> np.ndarray:
        """
        Calculates relative parameters [p, t, j, c] using Formulas (5)–(8):
        p = Pmin / P
        t = Tmin / T
        j = Jmin / J
        c = C / Cmax
        """
        p = self.P_min / max(0.01, loss_pct)
        t = self.T_min / max(1.0, delay_ms)
        j = self.J_min / max(0.5, jitter_ms)
        c = bw_kbps / self.C_max
        return np.array([p, t, j, c], dtype=float)

    def compute_all_relative_priorities(self, sla_boost_user_id: int = None) -> Dict[str, float]:
        """
        Computes Formula (9) for all 6 service classes:
        Pr_i = sum_j (X_ij * Y_ij * Z_j) / sum_i sum_j (X_ij * Y_ij * Z_j)
        """
        numerator_list = []
        class_keys = ['A', 'B', 'C', 'D', 'E', 'F']

        for c_key in class_keys:
            cfg = self.classes_cfg[c_key]
            # Baseline QoS requirements from Table I
            loss_req = cfg['loss_limit_percent']
            delay_req = cfg['delay_limit_ms']
            jitter_req = cfg['jitter_limit_ms']
            bw_req = cfg['bandwidth_kbps']

            # X_ij vector from relative formulas (5)-(8)
            X_i = self.calculate_relative_qos_vector(loss_req, delay_req, jitter_req, bw_req)

            # Y_ij vector from Table II
            Y_i = np.array(cfg['importance'], dtype=float)

            # Check if this class receives an SLA boost (e.g. for User 7's IPTV Class C)
            if sla_boost_user_id is not None and c_key == 'C':
                # Controller temporarily increases SLA priority weight for degraded IPTV service
                X_i[0] *= 1.8  # Increase loss priority
                X_i[1] *= 1.5  # Increase delay priority
                Y_i[0] = 3.0   # Highest importance

            # Numerator for class i: sum_j(X_ij * Y_ij * Z_j)
            num_i = np.sum(X_i * Y_i * self.Z)
            numerator_list.append(num_i)

        total_sum = sum(numerator_list)
        priorities = {}
        for idx, c_key in enumerate(class_keys):
            priorities[c_key] = numerator_list[idx] / total_sum

        return priorities

    def assign_flow_priorities(self, flows: List[Any], degraded_user_id: int = None):
        """
        Assigns relative priorities, categories (1, 2, 3), and DSCP codes to flows.
        """
        priorities = self.compute_all_relative_priorities(sla_boost_user_id=degraded_user_id)

        for flow in flows:
            c_key = flow.service_class
            base_pri = priorities[c_key]
            
            # If this is specifically User 7 experiencing degradation, boost its priority directly
            if degraded_user_id is not None and flow.user_id == degraded_user_id:
                flow.relative_priority = min(1.0, base_pri * 1.45)
                flow.assigned_category = 1  # Elevated to Category 1 for strict protection
                flow.dscp_code = "111000"   # High critical priority bits set
            else:
                flow.relative_priority = base_pri
                flow.assigned_category = self.classes_cfg[c_key]['category']
                
                # Encode binary DSCP code starting with 001
                if flow.assigned_category == 1:
                    flow.dscp_code = "001100"
                elif flow.assigned_category == 2:
                    flow.dscp_code = "001010"
                else:
                    flow.dscp_code = "001001"
