import sys
from argparse import ArgumentParser
from spectroscopy.utilities import eigenvectors_to_eigendisplacements
from spectroscopy.interfaces.phonopy_interface import read_born
from spectroscopy.cli.parser import update_parser, post_process_args
from spectroscopy.cli.phonopy_helper import (
    phonopy_update_parser, phonopy_load_core, phonopy_load_optional)
from spectroscopy.cli.runtime import run_mode_ir

def main():
    parser = ArgumentParser(
        description="Simulate IR spectra from Phonopy calculations")
    phonopy_update_parser(parser, 'ir')
    args = parser.parse_args()
    post_process_args(args, 'ir')

    input_data = phonopy_load_core(
        args, extract_list=['structure', 'atomic_masses', 'phonon_modes'])
    structure = input_data['structure']
    atomic_masses = input_data['atomic_masses']
    frequencies, eigenvectors = input_data['phonon_modes']

    input_data = phonopy_load_optional(args)
    irrep_data = input_data.get('irrep_data')
    linewidths = input_data.get('linewidths')

    eigendisplacements = eigenvectors_to_eigendisplacements(
        eigenvectors, atomic_masses)

    bec_tensors = read_born(structure, file_path=args.BORNFile)

    run_mode_ir(
        frequencies, eigendisplacements, bec_tensors, args,
        linewidths=linewidths, irrep_data=irrep_data
        )

if __name__ == "__main__":
    main()
