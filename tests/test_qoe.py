"""
Unit Tests for QoS/QoE Evaluation Module
Verifies Formula (20), Tables IV & V, and empirical QoE mapping.
"""

import unittest
import numpy as np

from src.qos_qoe import QoEEvaluator

class TestQoE(unittest.TestCase):
    def setUp(self):
        self.evaluator = QoEEvaluator()

    def test_formula_20_integral_qos(self):
        """Verifies Formula (20) behaves monotonically: better network metrics yield smaller QoS(x)."""
        # Optimal parameters
        qos_good = self.evaluator.calculate_qos_integral(loss_pct=0.1, delay_ms=100.0, jitter_ms=10.0, bw_mbps=10.0)
        # Degraded parameters
        qos_bad = self.evaluator.calculate_qos_integral(loss_pct=2.0, delay_ms=250.0, jitter_ms=55.0, bw_mbps=1.0)
        
        self.assertLess(qos_good, qos_bad)
        self.assertGreaterEqual(qos_good, 0.0)
        self.assertLessEqual(qos_bad, 1.0)

    def test_qoe_mapping_bounds(self):
        """Verifies QoE values always fall within [1.0, 5.0] on the MOS scale."""
        for qos_val in np.linspace(0.0, 1.0, 20):
            qoe = self.evaluator.calculate_qoe_from_qos(qos_val)
            self.assertGreaterEqual(qoe, 1.0)
            self.assertLessEqual(qoe, 5.0)

    def test_table_iv_classification(self):
        """Verifies Table IV expert evaluation categories."""
        # Good: delay < 150, jitter <= 20, loss <= 1, bw >= 2
        res_good = self.evaluator.evaluate_live_video_qoe(loss_pct=0.5, delay_ms=120.0, jitter_ms=15.0, bw_mbps=5.0)
        self.assertEqual(res_good['satisfaction_category'], "Good")
        self.assertGreaterEqual(res_good['qoe_score'], 4.0)

        # Bad: delay > 200 or jitter > 50 or loss > 2 or bw < 1
        res_bad = self.evaluator.evaluate_live_video_qoe(loss_pct=2.2, delay_ms=260.0, jitter_ms=55.0, bw_mbps=0.8)
        self.assertEqual(res_bad['satisfaction_category'], "Bad")
        self.assertLess(res_bad['qoe_score'], 3.0)
        self.assertEqual(res_bad['alert_color'], "red")

if __name__ == '__main__':
    unittest.main()
