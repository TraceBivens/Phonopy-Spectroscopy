# -*- coding: utf-8 -*-
import os
import unittest
import numpy as np
from phonopy_spectroscopy.raman.finite_diff import FiniteDisplacementRamanTensorCalculator
from phonopy_spectroscopy.interfaces.phonopy_interface import gamma_phonons_from_phono3py

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_LEGACY_YAML = os.path.join(_TEST_DIR, "..", "example", "legacy-disp-si", "Raman.yaml")
_EXAMPLE_SI = os.path.join(_TEST_DIR, "..", "example", "si")

class TestLegacyRaman(unittest.TestCase):
    def test_from_legacy_yaml(self):
        gamma_ph = gamma_phonons_from_phono3py(
            os.path.join(_EXAMPLE_SI, "phonopy.yaml"),
            os.path.join(_EXAMPLE_SI, "mesh.yaml")
        )
        
        calc = FiniteDisplacementRamanTensorCalculator.from_legacy_yaml(gamma_ph, _LEGACY_YAML)
        
        # Check band indices (should be 4, 5, 6 in file -> 3, 4, 5 in 0-indexed)
        self.assertEqual(calc.band_indices.tolist(), [3, 4, 5])
        self.assertEqual(calc.num_bands, 3)
        
        # Check step sizes
        self.assertIsNotNone(calc._step_size_matrix)
        self.assertEqual(len(calc._step_size_matrix), 3)
        
        # Check displacement_step: ±0.05299575
        for step in calc._step_size_matrix:
            self.assertAlmostEqual(step, 0.05299575)

if __name__ == "__main__":
    unittest.main()
