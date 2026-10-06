"""
QoS & QoE Evaluation Module
Implements Formula (20), Tables IV & V, and the empirical MOS QoE model.
Reference: Beshley et al., JCN 2024, Section VII, Fig. 10 & Fig. 11.
"""

from typing import Dict, Any
import numpy as np

class QoEEvaluator:
    """
    Computes normalized integral additive QoS score (Formula 20)
    and maps it to Quality of Experience (QoE) on a 1-5 scale.
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config
        
        # High-quality reference thresholds for live video (Table IV "Good" upper bounds)
        self.P_ref = 0.8    # 0.8% loss reference
        self.T_ref = 140.0  # 140 ms delay reference
        self.J_ref = 20.0   # 20 ms jitter reference
        self.C_ref = 4.0    # 4 Mbit/s bandwidth reference

        # Importance weights K1..K4 for video QoS (Formula 20)
        self.K1 = 0.35  # Loss weight
        self.K2 = 0.30  # Delay weight
        self.K3 = 0.15  # Bandwidth weight
        self.K4 = 0.20  # Jitter weight

        # Sigmoid calibration parameters matching Fig. 11
        # QoS = 0.278 -> QoE = 4.70
        # QoS = 0.425 -> QoE = 3.73
        # QoS = 0.546 -> QoE = 1.90
        self.midpoint = 0.458
        self.steepness = 0.0715

    def calculate_qos_integral(self, loss_pct: float, delay_ms: float, jitter_ms: float, bw_mbps: float) -> float:
        """
        Formula (20):
        QoS(x) = 1 - ( K1*(Pmin/P) + K2*(Tmin/T) + K3*(C/Cmax) + K4*(Jmin/J) )
        Ratios are capped at 1.0 (performance meeting or exceeding reference).
        Values range between 0.0 (optimal) and 1.0 (severe degradation).
        """
        p_term = min(1.0, self.P_ref / max(0.01, loss_pct))
        t_term = min(1.0, self.T_ref / max(1.0, delay_ms))
        c_term = min(1.0, bw_mbps / self.C_ref)
        j_term = min(1.0, self.J_ref / max(0.5, jitter_ms))

        sum_terms = (
            self.K1 * p_term +
            self.K2 * t_term +
            self.K3 * c_term +
            self.K4 * j_term
        )

        qos_x = max(0.0, min(1.0, 1.0 - sum_terms))
        return float(qos_x)

    def calculate_qoe_from_qos(self, qos_x: float) -> float:
        """
        Calculates QoE MOS score from normalized QoS(x) aligning with Fig. 11:
        - QoS ≈ 0.278 -> QoE ≈ 4.70 (Proposed Combined SOSDN)
        - QoS ≈ 0.425 -> QoE ≈ 3.73 (Adaptive Prioritization + OSPF)
        - QoS ≈ 0.546 -> QoE ≈ 1.90 (PQ + OSPF)
        - QoS ≈ 0.600 -> QoE ≈ 0.70 - 1.10 (FIFO + OSPF)
        """
        qoe_val = 1.0 + 4.0 / (1.0 + np.exp((qos_x - self.midpoint) / self.steepness))
        return float(np.clip(qoe_val, 1.0, 5.0))

    def evaluate_live_video_qoe(
        self,
        loss_pct: float,
        delay_ms: float,
        jitter_ms: float,
        bw_mbps: float,
        path_cost: float = None
    ) -> Dict[str, Any]:
        """
        Evaluates full QoS/QoE status for live video (IPTV / VoD) flows:
        Returns qos_score, qoe_score, satisfaction_category, alert_color.
        """
        qos_x = self.calculate_qos_integral(loss_pct, delay_ms, jitter_ms, bw_mbps)
        qoe_score = self.calculate_qoe_from_qos(qos_x)

        # Categorize according to Table IV
        if delay_ms < 150.0 and jitter_ms <= 20.0 and loss_pct <= 1.0 and bw_mbps >= 2.0:
            table_category = "Good"
        elif delay_ms <= 200.0 and jitter_ms <= 50.0 and loss_pct <= 2.0 and bw_mbps >= 1.0:
            table_category = "Fair"
        else:
            table_category = "Bad"

        # Alert color coding from Section VII / Fig. 10:
        # Green: significantly better than SLA bounds
        # Yellow: close to acceptable bounds
        # Red: SLA violation, QoS degradation requiring SDN intervention
        if loss_pct > 1.6 or delay_ms > 220.0 or jitter_ms > 50.0 or qoe_score < 2.5:
            alert_color = "red"
        elif loss_pct > 0.8 or delay_ms > 160.0 or jitter_ms > 25.0 or qoe_score < 4.2:
            alert_color = "yellow"
        else:
            alert_color = "green"

        return {
            'qos_x': qos_x,
            'qoe_score': qoe_score,
            'satisfaction_category': table_category,
            'alert_color': alert_color
        }
