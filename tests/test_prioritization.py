"""
Unit Tests for Adaptive Prioritization Module
Verifies Formulas (5)–(9), normalization, and SLA elevation.
"""

import unittest
import numpy as np
import yaml
import os

from src.prioritization import AdaptivePrioritization

class TestPrioritization(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg_path = os.path.join(base_dir, 'config', 'experiment_config.yaml')
        with open(cfg_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.prioritizer = AdaptivePrioritization(self.config)

    def test_relative_parameter_formulas(self):
        """Tests Formulas (5)–(8) relative parameter calculations."""
        loss_pct, delay_ms, jitter_ms, bw_kbps = 0.25, 150.0, 10.0, 64.0
        vec = self.prioritizer.calculate_relative_qos_vector(loss_pct, delay_ms, jitter_ms, bw_kbps)
        
        # p = P_min / P = 0.1 / 0.25 = 0.4
        self.assertAlmostEqual(vec[0], 0.4, places=2)
        # t = T_min / T = 100 / 150 = 0.6667
        self.assertAlmostEqual(vec[1], 100.0 / 150.0, places=2)
        # j = J_min / J = 10 / 10 = 1.0
        self.assertAlmostEqual(vec[2], 1.0, places=2)
        # c = C / C_max = 64 / 10000 = 0.0064
        self.assertAlmostEqual(vec[3], 0.0064, places=4)

    def test_formula_9_normalization(self):
        """Verifies that sum of all relative priorities Pr_i across 6 classes equals 1.0."""
        priorities = self.prioritizer.compute_all_relative_priorities()
        self.assertEqual(len(priorities), 6)
        total_pr = sum(priorities.values())
        self.assertAlmostEqual(total_pr, 1.0, places=5)
        
        # Every priority must be bounded between 0 and 1
        for c, pr in priorities.items():
            self.assertGreater(pr, 0.0)
            self.assertLess(pr, 1.0)

    def test_sla_boost(self):
        """Verifies that an SLA boost elevates IPTV priority when requested."""
        base_priorities = self.prioritizer.compute_all_relative_priorities()
        boosted_priorities = self.prioritizer.compute_all_relative_priorities(sla_boost_user_id=7)
        
        # Class C (IPTV) priority should increase after boost
        self.assertGreater(boosted_priorities['C'], base_priorities['C'])

if __name__ == '__main__':
    unittest.main()
