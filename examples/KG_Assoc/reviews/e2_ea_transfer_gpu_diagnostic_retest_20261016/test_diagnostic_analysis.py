"""Deterministic forensic checks, not numerical acceptance of the failed retest."""
import math
import unittest
from reproduce import float32, velocity_audit


class DiagnosticAnalysisTests(unittest.TestCase):
    def test_serialized_double_and_loader_float_are_distinct(self):
        self.assertEqual(float32(.270623), .27062299847602844)
        self.assertNotEqual(float32(.270623), .270623)

    def test_saved_failure_pattern_has_correct_actual_and_wrong_expected(self):
        original = [.270623, .266728, .876108]
        represented = [float32(x) for x in original]
        recorded = original[:2] + represented[2:]
        audit = velocity_audit(original, recorded, represented)
        self.assertEqual(audit['actual_matches_represented'], [True]*3)
        self.assertEqual(audit['recorded_expected_matches_represented'], [False, False, True])

    def test_actual_one_float_step_corruption_is_not_tolerated(self):
        audit = velocity_audit([1., 2., 3.], [1., 2., 3.], [1.+2**-23, 2., 3.])
        self.assertEqual(audit['actual_matches_represented'], [False, True, True])

    def test_correctly_rounded_expected_and_actual_match_exactly(self):
        original = [-.270623, 0., 2.876108]
        represented = [float32(x) for x in original]
        audit = velocity_audit(original, represented, represented)
        self.assertEqual(audit['signed_native_comparison_error'], [0., 0., 0.])
        self.assertEqual(audit['recorded_expected_matches_represented'], [True]*3)

    def test_nonfinite_evidence_is_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(AssertionError):
                velocity_audit([0., 0., 0.], [value, 0., 0.], [0., 0., 0.])


if __name__ == '__main__':
    unittest.main()
