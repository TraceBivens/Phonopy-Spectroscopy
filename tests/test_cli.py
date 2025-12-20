# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch
import sys
import pandas as pd
import numpy as np

from phonopy_spectroscopy.cli.main_ir import main as main_ir
from phonopy_spectroscopy.cli.main_raman import main as main_raman

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_EXAMPLE_SI = os.path.join(_TEST_DIR, "..", "example", "si")
_EXAMPLE_SNSE = os.path.join(_TEST_DIR, "..", "example", "snse-pnma")

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Change directory to project root or something consistent if needed
        # But we use absolute paths for examples, so it should be fine.
        pass

    @patch("sys.argv", ["phonopy-ir", "--help"])
    def test_ir_help(self):
        with self.assertRaises(SystemExit) as cm:
            main_ir()
        self.assertEqual(cm.exception.code, 0)

    @patch("sys.argv", ["phonopy-raman", "--help"])
    def test_raman_help(self):
        with self.assertRaises(SystemExit) as cm:
            main_raman()
        self.assertEqual(cm.exception.code, 0)

    @patch("matplotlib.pyplot.show")
    def test_ir_full_run(self, mock_show):
        output_file = "test_ir_spectrum.dat"
        if os.path.exists(output_file):
            os.remove(output_file)
            
        test_args = [
            "phonopy-ir",
            "--cell", os.path.join(_EXAMPLE_SNSE, "POSCAR.Opt"),
            "--freqs-evecs", os.path.join(_EXAMPLE_SNSE, "mesh.yaml"),
            "--irreps", os.path.join(_EXAMPLE_SNSE, "irreps.yaml"),
            "--born", os.path.join(_EXAMPLE_SNSE, "BORN"),
            "--lws-file", os.path.join(_EXAMPLE_SNSE, "kappa-m16816.Prim.FullPP.hdf5"),
            "--range", "0", "10",
            "--output", output_file,
            "--plot"
        ]
        
        with patch("sys.argv", test_args):
            main_ir()
            
        self.assertTrue(os.path.exists(output_file))
        df = pd.read_csv(output_file)
        self.assertIn("freq_energy", df.columns)
        self.assertIn("eps_im", df.columns)
        self.assertTrue(mock_show.called)
        
        if os.path.exists(output_file):
            os.remove(output_file)

    @patch("matplotlib.pyplot.show")
    def test_raman_disp_run(self, mock_show):
        test_args = [
            "phonopy-raman",
            "--cell", os.path.join(_EXAMPLE_SI, "POSCAR.Opt.Prim"),
            "--freqs-evecs", os.path.join(_EXAMPLE_SI, "mesh.yaml"),
            "--irreps", os.path.join(_EXAMPLE_SI, "irreps.yaml"),
            "raman-disp",
            "--distance", "0.01"
        ]
        
        # Clean up existing POSCAR files if any
        import glob
        for f in glob.glob("POSCAR-*-*"):
            os.remove(f)
            
        with patch("sys.argv", test_args):
            main_raman()
            
        poscars = glob.glob("POSCAR-*-*")
        self.assertGreater(len(poscars), 0)
        
        # Cleanup
        for f in poscars:
            os.remove(f)

    @patch("matplotlib.pyplot.show")
    def test_raman_read_run(self, mock_show):
        output_file = "test_raman_spectrum.dat"
        if os.path.exists(output_file):
            os.remove(output_file)
            
        dielectric_pattern = os.path.join(_EXAMPLE_SI, "raman_ref", "vasprun-PBEsol-DFPT-*-*.xml")
        import glob
        dielectric_files = glob.glob(dielectric_pattern)
        
        test_args = [
            "phonopy-raman",
            "--cell", os.path.join(_EXAMPLE_SI, "POSCAR.Opt.Prim"),
            "--freqs-evecs", os.path.join(_EXAMPLE_SI, "mesh.yaml"),
            "--irreps", os.path.join(_EXAMPLE_SI, "irreps.yaml"),
            "--range", "0", "20",
            "--output", output_file,
            "--plot",
            "raman-read",
            "--dielectric"
        ] + dielectric_files

        with patch("sys.argv", test_args):
            main_raman()
            
        self.assertTrue(os.path.exists(output_file))
        df = pd.read_csv(output_file)
        self.assertIn("freq_energy", df.columns)
        self.assertTrue(mock_show.called)
        
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    unittest.main()
