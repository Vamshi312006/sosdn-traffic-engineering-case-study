"""
Unit Tests for Server Selection Module
Verifies Formula (19) and Table III numerical calculations from Beshley et al.
"""

import unittest
import numpy as np

class TestServerSelection(unittest.TestCase):
    def test_paper_table_iii_verbatim(self):
        """
        Directly validates the Azure 3-server example from Section VI:
        Table III:
        Criteria:
        1. CPU load: alpha_1 = 0.3, S1 = 60, S2 = 70, S3 = 50, best min f_1^0 = 50
        2. RAM load: alpha_2 = 0.2, S1 = 50, S2 = 30, S3 = 60, best min f_2^0 = 30
        3. Processing time: alpha_3 = 0.2, S1 = 100, S2 = 150, S3 = 400, best min f_3^0 = 100
        4. Drop prob: alpha_4 = 0.2, S1 = 0.3 (or 0.5), S2 = 0.8, S3 = 0.3, best min f_4^0 = 0.3
        5. NIC load: alpha_5 = 0.1, S1 = 80, S2 = 70, S3 = 60, best min f_5^0 = 60
        """
        alpha = np.array([0.3, 0.2, 0.2, 0.2, 0.1])
        self.assertAlmostEqual(np.sum(alpha), 1.0, places=5)

        f_0 = np.array([50.0, 30.0, 100.0, 0.3, 60.0])

        # Paper evaluated values:
        # Server 1: 0.3*(50/60) + 0.2*(30/50) + 0.2*(100/100) + 0.2*(0.3/0.3) + 0.1*(60/80) = 0.845
        vec_s1 = np.array([60.0, 50.0, 100.0, 0.3, 80.0])
        f_s1 = np.sum(alpha * (f_0 / vec_s1))
        self.assertAlmostEqual(f_s1, 0.845, places=2)

        # Server 2: 0.3*(50/70) + 0.2*(30/30) + 0.2*(100/150) + 0.2*(0.3/0.8) + 0.1*(60/70) = 0.708 (paper rounds to 0.707)
        vec_s2 = np.array([70.0, 30.0, 150.0, 0.8, 70.0])
        f_s2 = np.sum(alpha * (f_0 / vec_s2))
        self.assertAlmostEqual(f_s2, 0.707, places=2)

        # Server 3: 0.3*(50/50) + 0.2*(30/60) + 0.2*(100/400) + 0.2*(0.3/0.3) + 0.1*(60/60) = 0.750
        vec_s3 = np.array([50.0, 60.0, 400.0, 0.3, 60.0])
        f_s3 = np.sum(alpha * (f_0 / vec_s3))
        self.assertAlmostEqual(f_s3, 0.750, places=2)

        # Confirm Server 1 is optimal
        best_server = np.argmax([f_s1, f_s2, f_s3]) + 1
        self.assertEqual(best_server, 1)

if __name__ == '__main__':
    unittest.main()
