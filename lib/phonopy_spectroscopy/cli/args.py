# -*- coding: utf-8 -*-


# ---------
# Docstring
# ---------


"""Routines implementing command-line argument handling."""


# -------
# Imports
# -------


from argparse import ArgumentParser


# ------------
# Parser setup
# ------------


def parser_init():
    """Initialise a command-line argument parser with common arguments."""

    parser = ArgumentParser()

    parser.add_argument(
        "--cell",
        dest="cell_file",
        type=str,
        default="phonopy.yaml",
        help="Crystal structure (e.g. phonopy.yaml or POSCAR)",
    )

    parser.add_argument(
        "--freqs-evecs",
        dest="freqs_evecs_file",
        type=str,
        default=None,
        help=(
            "Frequencies and eigenvectors (default: mesh.yaml, "
            "mesh.hdf5, band.yaml, or band.hdf5)"
        ),
    )

    parser.add_argument(
        "--lw",
        "--linewidth",
        dest="linewidth",
        type=float,
        default=None,
        help=(
            "Uniform linewidth or scale factor for calculated "
            "linewidths (default: 0.5 THz or 1.0)"
        ),
    )

    parser.add_argument(
        "--lws-file",
        dest="linewidths_file",
        type=str,
        default=None,
        help="Linewidths (kappa-m*.hdf5 or kappa-m*-g*.hdf5)",
    )

    parser.add_argument(
        "--lws-temp",
        dest="linewidths_temp",
        type=float,
        default=300.0,
        help="Temperature for loading linewidths (default: 300 K)",
    )

    parser.add_argument(
        "--irreps",
        dest="irreps_file",
        type=str,
        default="irreps.yaml",
        help="Irreps (irreps.yaml)",
    )

    parser.add_argument(
        "--range",
        dest="spectrum_range",
        type=float,
        nargs=2,
        default=None,
        help="Frequency range for spectrum (min max)",
    )

    parser.add_argument(
        "--step",
        dest="spectrum_step",
        type=float,
        default=None,
        help="Frequency step for spectrum",
    )

    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        type=str,
        default=None,
        help="Output filename for spectrum data",
    )

    parser.add_argument(
        "--plot",
        dest="plot_spectrum",
        action="store_true",
        help="Plot the simulated spectrum",
    )

    parser.add_argument(
        "--wavelength",
        "-w",
        dest="wavelength",
        type=float,
        default=532.0,
        help="Laser wavelength in nm (default: 532 nm)",
    )

    parser.add_argument(
        "--temp",
        dest="temperature",
        type=float,
        default=300.0,
        help="Temperature for intensity scaling (default: 300 K)",
    )

    parser.add_argument(
        "--units",
        "-u",
        dest="units",
        type=str,
        default="inv_cm",
        choices=["thz", "inv_cm", "ev", "mev"],
        help="Frequency/energy units for the spectrum (default: inv_cm)",
    )

    return parser


def parser_update_ir(parser):
    """Add IR-specific arguments to a parser."""

    parser.add_argument(
        "--born",
        dest="born_file",
        type=str,
        default="BORN",
        help="Born charges and high-frequency dielectric constant (BORN)",
    )

    parser.add_argument(
        "--eps-hf",
        dest="epsilon_inf",
        type=str,
        default=None,
        help="High-frequency dielectric constant",
    )

    return parser

def parser_update_raman(parser):
    """Add Raman-specific arguments to a parser."""

    parser.add_argument(
        "--displace",
        "-d",
        dest="displace",
        nargs="?",
        const=True,
        default=False,
        help=(
            "Generate displaced structures for Raman tensors. "
            "Optional argument: crystal structure file (default: value "
            "of --cell)."
        ),
    )

    parser.add_argument(
        "--amplitude",
        "-a",
        dest="amplitude",
        type=float,
        default=0.01,
        help="Displacement magnitude (default: 0.01 Angstrom)",
    )

    parser.add_argument(
        "--prec",
        dest="precision",
        type=int,
        default=2,
        help="Precision of central-difference scheme (default: 2)",
    )

    parser.add_argument(
        "--post-process",
        "-p",
        dest="post_process",
        type=str,
        nargs="+",
        help="Post-process dielectric function data files (e.g. vasprun.xml)",
    )

    return parser


# ---------------
# Post processing
# ---------------


def args_post_proc(args):
    """Post-process common arguments."""

    # We allow spectrum_range and spectrum_step to be None, so that the
    # libraries' automatic range/resolution detection can be used.

    return args


def args_post_proc_ir(args):
    """Post-process IR-specific arguments."""
    args = args_post_proc(args)
    return args


def args_post_proc_raman(args):
    """Post-process Raman-specific arguments."""
    args = args_post_proc(args)
    return args
