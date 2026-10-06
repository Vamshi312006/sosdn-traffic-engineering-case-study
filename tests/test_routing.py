"""
Unit Tests for Routing Module
Verifies Formulas (12)–(18), metric W(i,j), and multi-criteria path selection.
"""

import unittest
import numpy as np
import yaml
import os

from src.topology import SOSDNTopology
from src.routing import MultiCriteriaRouter

class TestRouting(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg_path = os.path.join(base_dir, 'config', 'experiment_config.yaml')
        with open(cfg_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.topology = SOSDNTopology(self.config)
        self.router = MultiCriteriaRouter(self.config, self.topology)

    def test_weight_constraints_formula_18(self):
        """Verifies Formula (18): sum(X_k) == 1 and 0 <= X_k <= 1 for all categories."""
        for cat in [1, 2, 3]:
            w = self.router.get_category_weights(cat)
            self.assertEqual(len(w), 4)
            self.assertAlmostEqual(np.sum(w), 1.0, places=5)
            self.assertTrue(np.all(w >= 0.0))
            self.assertTrue(np.all(w <= 1.0))

    def test_link_metric_calculation_formula_16(self):
        """Verifies that W_ij is calculated and stays bounded in [0, 1]."""
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        link_metrics = self.router.compute_link_metrics(weights)
        self.assertGreater(len(link_metrics), 0)
        
        for (u, v), cost in link_metrics.items():
            self.assertGreaterEqual(cost, 0.0)
            self.assertLessEqual(cost, 1.0)

    def test_path_selection(self):
        """Verifies that OSPF and MultiCriteria routing find valid paths between switches."""
        src = "SW1_E1"
        dst = "SW4_E2"
        
        ospf_path = self.router.find_ospf_path(src, dst)
        self.assertIsInstance(ospf_path, list)
        self.assertEqual(ospf_path[0], src)
        self.assertEqual(ospf_path[-1], dst)

        mc_path, cost = self.router.find_multicriteria_path(src, dst, category=2)
        self.assertIsInstance(mc_path, list)
        self.assertEqual(mc_path[0], src)
        self.assertEqual(mc_path[-1], dst)
        self.assertGreater(cost, 0.0)

if __name__ == '__main__':
    unittest.main()
