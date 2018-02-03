from unittest import TestCase

import dateutil

class TestSolver(TestCase):
    def test_get_next_month(self):
        self.assertEqual(dateutil.get_next_month(current=0))
