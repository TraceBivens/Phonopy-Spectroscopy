# -*- coding: utf-8 -*-
import sys
import os
import matplotlib.pyplot as plt

from phonopy_spectroscopy.cli.args import (
    parser_init,
    parser_update_raman,
    args_post_proc_raman,
)
from phonopy_spectroscopy.interfaces.phonopy_interface import (
    gamma_phonons_from_phono3py,
)
from phonopy_spectroscopy.raman.finite_diff import (
    FiniteDisplacementRamanTensorCalculator,
)
from phonopy_spectroscopy.cli.utility.raman_io import (
    fd_read_dielectrics_vasp,
)

def main():
    parser = parser_init()
    parser = parser_update_raman(parser)
    args = parser.parse_args()
    args = args_post_proc_raman(args)

    if args.mode is None:
        parser.print_help()
        sys.exit(0)

    print(f"Phonopy-Raman: Starting mode {args.mode}...")

    # Load phonons (needed for both modes)
    if not os.path.exists(args.cell_file):
        print(f"Error: Cell file '{args.cell_file}' not found.")
        sys.exit(1)
    
    if args.freqs_evecs_file is None:
        for f in ["mesh.yaml", "mesh.hdf5", "phonopy.yaml", "POSCAR"]:
             # If cell_file is phonopy.yaml, we might not need separate freqs_evecs
             if args.cell_file.endswith(".yaml"):
                 args.freqs_evecs_file = args.cell_file
                 break
             if os.path.exists(f):
                args.freqs_evecs_file = f
                break

    if args.freqs_evecs_file is None:
        print("Error: No frequencies/eigenvectors file specified or found.")
        sys.exit(1)

    print(f"  Loading phonons from {args.freqs_evecs_file}...")
    gamma_ph = gamma_phonons_from_phono3py(
        args.cell_file,
        args.freqs_evecs_file,
        lws_file=args.linewidths_file,
        lws_t=args.linewidths_temp,
        irreps_file=args.irreps_file,
    )

    if args.mode == "raman-disp":
        from phonopy_spectroscopy.interfaces.vasp_interface import (
            structure_to_poscar,
        )

        fd_calc = FiniteDisplacementRamanTensorCalculator(
            gamma_ph, step_size=args.distance, prec=2, band_inds="active"
        )

        print(
            f"  Generating displacements for {fd_calc.num_bands} bands and {fd_calc.num_steps} steps..."
        )
        disp_structs = fd_calc.generate_displaced_structures()

        # Save structures
        for i, b_idx in enumerate(fd_calc.band_indices):
            for j, step in enumerate(fd_calc.displacement_steps):
                filename = f"POSCAR-{b_idx+1:04d}-{j+1:02d}"
                structure_to_poscar(
                    disp_structs[i, j],
                    filename,
                    system_name=f"Band {b_idx+1} Step {j+1}",
                )
        print(f"  Finished generating {fd_calc.num_bands * fd_calc.num_steps} structures.")

    elif args.mode == "raman-read":
        from phonopy_spectroscopy.cli.utility.raman_io import (
            fd_read_dielectrics_vasp,
        )

        fd_calc = FiniteDisplacementRamanTensorCalculator(
            gamma_ph, step_size=args.distance, prec=2, band_inds="active"
        )

        if not args.dielectric_files:
            print("Error: No dielectric data files specified.")
            sys.exit(1)

        print(f"  Reading {len(args.dielectric_files)} dielectric files...")
        e, eps_e = fd_read_dielectrics_vasp(
            args.dielectric_files, fd_calc.num_bands, fd_calc.num_steps
        )

        # calculate_raman_tensors returns a RamanCalculation object
        print("  Calculating Raman tensors...")
        raman_calc = fd_calc.calculate_raman_tensors(eps_e, e)

        # Calculate powder Raman spectrum
        from phonopy_spectroscopy.instrument import Geometry, Polarisation

        geom = Geometry("z", "-z")
        i_pol = Polarisation.from_direction("x")
        s_pol = "parallel"

        print(
            f"  Calculating spectrum in range {args.spectrum_range} THz with step {args.spectrum_step} THz..."
        )
        spectrum = raman_calc.powder(
            geom,
            i_pol,
            s_pol,
            lw=args.linewidth,
            x_range=args.spectrum_range,
            x_res=args.spectrum_step,
            w=args.wavelength,
            t=args.temperature,
        )

        spectrum_df = spectrum.spectrum()

        # Save results
        output_file = args.output_file if args.output_file else "raman.dat"
        print(f"  Saving results to {output_file}...")
        spectrum_df.to_csv(output_file, index=False)

        # Plot results
        if args.plot_spectrum:
            print("  Plotting spectrum...")
            # int_col depends on name but usually 'int' or 'cross_sect'
            int_col = spectrum._get_data_frame_column_headers()[0]
            plt.figure()
            plt.plot(
                spectrum_df["freq_energy"],
                spectrum_df[int_col],
                label="Raman Intensity",
            )
            plt.xlabel(f"Frequency ({spectrum.x_unit_plot_label})")
            plt.ylabel(f"Intensity ({spectrum.y_unit_plot_label})")
            plt.legend()
            plt.title("Simulated Raman Spectrum (Powder)")
            plt.grid(True)
            plt.show()

    print("Phonopy-Raman: Finished.")

if __name__ == "__main__":
    main()
