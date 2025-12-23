# -*- coding: utf-8 -*-
import sys
import os
import matplotlib.pyplot as plt

from phonopy_spectroscopy.cli.args import (
    parser_init,
    parser_update_ir,
    args_post_proc_ir,
)
from phonopy_spectroscopy.interfaces.phonopy_interface import (
    gamma_phonons_from_phono3py,
    hf_dielectric_and_born_from_born,
)
from phonopy_spectroscopy.ir.calculation import InfraredCalculation

def main():
    parser = parser_init()
    parser = parser_update_ir(parser)
    args = parser.parse_args()
    args = args_post_proc_ir(args)

    print("Phonopy-IR: Starting infrared simulation...")

    # Load phonons
    if not os.path.exists(args.cell_file):
        print(f"Error: Cell file '{args.cell_file}' not found.")
        sys.exit(1)
    
    if args.freqs_evecs_file is None:
        # Try a list of standard phonopy output files
        for f in ["mesh.yaml", "mesh.hdf5", "band.yaml", "band.hdf5", "phonopy.yaml"]:
             if os.path.exists(f):
                args.freqs_evecs_file = f
                break

    if args.freqs_evecs_file is None:
        print("Error: No frequencies/eigenvectors file specified or found.")
        print("Please provide a file with --freqs-evecs.")
        sys.exit(1)

    irreps_file = args.irreps_file
    if irreps_file is None or not os.path.exists(irreps_file if irreps_file else ""):
        if os.path.exists("irreps.yaml"):
            irreps_file = "irreps.yaml"
        else:
            irreps_file = None

    print(f"  Loading phonons from {args.freqs_evecs_file}...")
    gamma_ph = gamma_phonons_from_phono3py(
        args.cell_file,
        args.freqs_evecs_file,
        lws_file=args.linewidths_file,
        lws_t=args.linewidths_temp,
        irreps_file=irreps_file,
    )

    if gamma_ph.has_irreps:
        active_irreps = gamma_ph.irreps.get_subset("ir").band_indices_flat()
        # Exclude acoustic modes
        acc_inds = gamma_ph.get_acoustic_mode_indices()
        active_inds = [idx for idx in active_irreps if idx not in acc_inds]
        print(f"  Identified {len(active_inds)} IR-active modes out of {gamma_ph.num_modes} total bands.")
    else:
        print("  Warning: Irreps not found. Mode filtering disabled.")
        print(f"  Using all {gamma_ph.num_modes - len(gamma_ph.get_acoustic_mode_indices())} optic modes.")

    # Load Born charges and eps_inf
    if not os.path.exists(args.born_file):
        print(f"Error: Born file '{args.born_file}' not found.")
        sys.exit(1)
    
    print(f"  Loading Born charges from {args.born_file}...")
    eps_inf, born_charges = hf_dielectric_and_born_from_born(
        args.born_file,
        gamma_ph.structure,
    )

    if args.epsilon_inf is not None:
        # Override eps_inf if provided (this might need parsing if it's a string)
        pass

    # Initialize calculation
    calc = InfraredCalculation(gamma_ph, born_charges, eps_inf=eps_inf)

    # Calculate spectrum
    print(f"  Calculating spectrum using {args.units} units...")
    
    from phonopy_spectroscopy.instrument import Geometry, Polarisation
    geom = Geometry("z", "-z")
    i_pol = Polarisation.from_direction("x")
    s_pol = i_pol
    
    # Calculate scalar powder dielectric function
    dielectric_func = calc.scalar_powder_dielectric_function(
        geom, i_pol, s_pol,
        lw=args.linewidth,
        x_range=args.spectrum_range,
        x_res=args.spectrum_step,
        x_units=args.units,
    )

    # Resolve range/step for printing if they were automatic
    x_min, x_max = dielectric_func.x[0], dielectric_func.x[-1]
    x_res = dielectric_func.x[1] - dielectric_func.x[0] if len(dielectric_func.x) > 1 else 0
    print(f"  Spectrum range: {x_min:.2f} to {x_max:.2f}, step: {x_res:.4f} ({args.units})")
    
    spectrum_df = dielectric_func.spectrum()

    # Save results
    if args.output_file:
        print(f"  Saving results to {args.output_file}...")
        spectrum_df.to_csv(args.output_file, index=False)
    else:
        # Default save to infrared.dat
        print("  Saving results to infrared.dat...")
        spectrum_df.to_csv("infrared.dat", index=False)

    # Plot results
    if args.plot_spectrum:
        print("  Plotting spectrum...")
        plt.figure()
        plt.plot(spectrum_df["freq_energy"], spectrum_df["eps_im"], label="Im(eps)")
        plt.xlabel(f"Frequency ({dielectric_func.x_unit_plot_label})")
        plt.ylabel("Intensity (Im(eps))")
        plt.legend()
        plt.title("Simulated Infrared Spectrum (Powder)")
        plt.grid(True)
        
        # Save plot
        plot_filename = f"{args.wavelength:g}.png"
        print(f"  Saving plot to {plot_filename}...")
        plt.savefig(plot_filename)
        plt.show()

    print("Phonopy-IR: Finished.")

if __name__ == "__main__":
    main()
