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
        # Try to find a default freqs/evecs file
        for f in ["mesh.yaml", "mesh.hdf5", "phonopy.yaml"]:
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
    print(f"  Calculating spectrum in range {args.spectrum_range} THz with step {args.spectrum_step} THz...")
    
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
    )
    
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
        plt.show()

    print("Phonopy-IR: Finished.")

if __name__ == "__main__":
    main()
