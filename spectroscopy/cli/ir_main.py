# -------
# Imports
# -------

from argparse import ArgumentParser

from spectroscopy.utilities import eigenvectors_to_eigendisplacements

from spectroscopy.cli.io_helper import (
    write_structures_ir, read_born_charges)

from spectroscopy.cli.parser import update_parser, post_process_args

from spectroscopy.cli.phonopy_helper import (
    phonopy_update_parser, phonopy_load_core, phonopy_load_optional)
                                    
from spectroscopy.cli.runtime import (
    run_mode_ir_disp, run_mode_ir_read, run_mode_ir_postproc)


# ----
# Main
# ----

def main():
    # Parse command-line arguments.

    parser = ArgumentParser(
        description="Simulate IR spectra starting from a Phonopy "
                    "calculation")

    # Add argument groups.

    phonopy_update_parser(parser, 'ir')
    
    # Parse and process arguments.

    args = parser.parse_args()

    post_process_args(args, 'ir')

    if args.RunMode is None:
        raise Exception(
            "Error: Please specify a run mode with one of the "
            "-d/--create_disp, -r/--read or -p/--post_process options.")

    elif args.RunMode == 'ir_disp':
        # Read input data.

        input_data = phonopy_load_core(
            args, extract_list=['structure', 'atomic_masses', 'phonon_modes'])

        structure = input_data['structure']
        atomic_masses = input_data['atomic_masses']
        frequencies, eigenvectors = input_data['phonon_modes']

        input_data = phonopy_load_optional(args)

        point_group = (input_data['point_group'] 
            if 'point_group' in input_data else None)

        irrep_data = (input_data['irrep_data'] 
            if 'irrep_data' in input_data else None)

        # Convert eigenvectors to eigendisplacements.

        eigendisplacements = eigenvectors_to_eigendisplacements(
            eigenvectors, atomic_masses)
        
        disp_sets = run_mode_ir_disp(
            structure, frequencies, eigendisplacements, args,
            point_group=point_group, irrep_data=irrep_data)

        write_structures_ir(
            disp_sets, file_format='vasp_poscar',
            output_prefix=args.OutputPrefix)

    elif args.RunMode == 'ir_read':
        born_charges = read_born_charges(
            args.BornInputFiles, file_format='vasp_outcar')

        run_mode_ir_read(born_charges, args)

    elif args.RunMode == 'ir_postproc':
        input_data = phonopy_load_optional(args)

        irrep_data = (input_data['irrep_data'] 
            if 'irrep_data' in input_data else None)
        
        linewidths = (input_data['linewidths'] 
            if 'linewidths' in input_data else None)

        run_mode_ir_postproc(
            args, linewidths=linewidths, irrep_data=irrep_data)


if __name__ == "__main__":
    main()