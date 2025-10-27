#!/usr/bin/env python

# -------
# Imports
# -------

from argparse import ArgumentParser

from spectroscopy.interfaces.misc import read_xyz
from spectroscopy.interfaces.vasp_interface import write_poscar


# ----
# Main
# ----

def main():
    # Parse command-line arguments.

    parser = ArgumentParser(
        description="Convert XYZ files to VASP POSCAR format")

    parser.add_argument(
        'input_file', type=str,
        help="Input XYZ file")

    parser.add_argument(
        '-o', '--output', type=str, default=None,
        help="Output POSCAR file (default: <input_file>.poscar)")

    # Parse arguments.

    args = parser.parse_args()

    # Read input file.

    structure = read_xyz(args.input_file)

    # Write output file.

    if args.output is None:
        output_file = args.input_file.rsplit('.', 1)[0] + '.poscar'
    else:
        output_file = args.output

    write_poscar(structure, output_file)


if __name__ == "__main__":
    main()