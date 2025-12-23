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
from phonopy_spectroscopy.utility.io_helper import (
    load_yaml,
    save_yaml,
)
from phonopy_spectroscopy.cli.utility.raman_io import (
    fd_read_dielectrics_vasp,
)

def main():
    parser = parser_init()
    parser = parser_update_raman(parser)
    args = parser.parse_args()
    args = args_post_proc_raman(args)

    if not (args.displace or args.post_process):
        parser.print_help()
        sys.exit(0)

    # Determine cell file to use
    cell_file = args.cell_file
    if isinstance(args.displace, str):
        cell_file = args.displace
    
    print(f"Phonopy-Raman: Starting simulation...")

    # Load phonons
    if not os.path.exists(cell_file):
        print(f"Error: Cell file '{cell_file}' not found.")
        sys.exit(1)
    
    freqs_evecs_file = args.freqs_evecs_file
    if freqs_evecs_file is None:
        # Try a list of standard phonopy output files
        for f in ["mesh.yaml", "mesh.hdf5", "band.yaml", "band.hdf5", "phonopy.yaml", "POSCAR"]:
             if os.path.exists(f):
                freqs_evecs_file = f
                break

    if freqs_evecs_file is None:
        print("Error: No frequencies/eigenvectors file specified or found.")
        print("Please provide a file with --freqs-evecs.")
        sys.exit(1)

    print(f"  Loading phonons from {freqs_evecs_file}...")
    irreps_file = args.irreps_file
    if irreps_file is None or not os.path.exists(irreps_file if irreps_file else ""):
        if os.path.exists("irreps.yaml"):
            irreps_file = "irreps.yaml"
        else:
            irreps_file = None

    gamma_ph = gamma_phonons_from_phono3py(
        cell_file,
        freqs_evecs_file,
        lws_file=args.linewidths_file,
        lws_t=args.linewidths_temp,
        irreps_file=irreps_file,
    )

    if gamma_ph.has_irreps:
        active_irreps = gamma_ph.irreps.get_subset("raman").band_indices_flat()
        # Exclude acoustic modes
        acc_inds = gamma_ph.get_acoustic_mode_indices()
        active_inds = [idx for idx in active_irreps if idx not in acc_inds]
        print(f"  Identified {len(active_inds)} Raman-active modes out of {gamma_ph.num_modes} total bands.")
    else:
        print("  Warning: Irreps not found. Mode filtering disabled.")
        print(f"  Using all {gamma_ph.num_modes - len(gamma_ph.get_acoustic_mode_indices())} optic modes.")

    if args.displace:
        from phonopy_spectroscopy.interfaces.vasp_interface import (
            structure_to_poscar,
        )

        fd_calc = FiniteDisplacementRamanTensorCalculator(
            gamma_ph, step_size=args.amplitude, prec=args.precision, band_inds="active"
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

        # Save metadata
        print(f"  Saving displacement metadata to raman_disp.yaml...")
        save_yaml(fd_calc.to_dict(), "raman_disp.yaml")

    if args.post_process:
        fd_calc = None
        if args.legacy:
            if os.path.exists(args.legacy):
                print(f"  Loading legacy displacement metadata from {args.legacy}...")
                fd_calc = FiniteDisplacementRamanTensorCalculator.from_legacy_yaml(
                    gamma_ph, args.legacy
                )
            else:
                print(f"  Error: Legacy metadata file '{args.legacy}' not found.")
                sys.exit(1)
        elif os.path.exists("raman_disp.yaml"):
            print("  Loading displacement metadata from raman_disp.yaml...")
            fd_calc = FiniteDisplacementRamanTensorCalculator.from_dict(
                load_yaml("raman_disp.yaml")
            )
            # Check for potential inconsistency with current phonon data
            if fd_calc.gamma_phonons.num_modes != gamma_ph.num_modes:
                 print("  Warning: Displacement metadata is for a different phonon calculation.")
                 print("           Proceeding with metadata settings...")
        else:
            print("  Warning: raman_disp.yaml not found. Parameters remain untracked.")
            print(f"           Using amplitude={args.amplitude}, prec={args.precision}.")
            fd_calc = FiniteDisplacementRamanTensorCalculator(
                gamma_ph,
                step_size=args.amplitude,
                prec=args.precision,
                band_inds="active",
            )

        print(f"  Reading {len(args.post_process)} dielectric files...")
        e, eps_e = fd_read_dielectrics_vasp(
            args.post_process, fd_calc.num_bands, fd_calc.num_steps
        )

        # calculate_raman_tensors returns a RamanCalculation object
        print("  Calculating Raman tensors...")
        if args.legacy:
            raman_calc = fd_calc.calculate_raman_tensors_legacy(eps_e, e)
        else:
            raman_calc = fd_calc.calculate_raman_tensors(eps_e, e)

        # Calculate powder Raman spectrum
        from phonopy_spectroscopy.instrument import Geometry, Polarisation

        geom = Geometry("z", "-z")
        i_pol = Polarisation.from_direction("x")
        s_pol = "parallel"

        print(f"  Calculating spectrum using {args.units} units...")
        spectrum = raman_calc.powder(
            geom,
            i_pol,
            s_pol,
            lw=args.linewidth,
            x_range=args.spectrum_range,
            x_res=args.spectrum_step,
            x_units=args.units,
            w=args.wavelength,
            t=args.temperature,
        )

        # Resolve range/step for printing if they were automatic
        x_min, x_max = spectrum.x[0], spectrum.x[-1]
        x_res = spectrum.x[1] - spectrum.x[0] if len(spectrum.x) > 1 else 0
        print(f"  Spectrum range: {x_min:.2f} to {x_max:.2f}, step: {x_res:.4f} ({args.units})")

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
            
            # Save plot
            plot_filename = f"{args.wavelength:g}.png"
            print(f"  Saving plot to {plot_filename}...")
            plt.savefig(plot_filename)
            plt.show()

    print("Phonopy-Raman: Finished.")

if __name__ == "__main__":
    main()
