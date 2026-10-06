#!/usr/bin/env python3
"""
Single-command automated experiment runner for SOSDN Case Study.
Executes the simulation, processes telemetry, and generates all result plots.
Usage:
    python run_experiment.py
"""

import sys
import os
import time

# Ensure src package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.experiment import run_experiment
from src.visualization import generate_all_plots

def main():
    start_time = time.time()
    print("======================================================================")
    print("  SOSDN CASE STUDY EXPERIMENT RUNNER")
    print("  Beshley et al., Journal of Communications and Networks, 2024")
    print("======================================================================")

    # 1. Run simulation
    df_raw, df_summary = run_experiment()

    # 2. Generate publication figures
    print("\n---> Generating Publication-Quality Figures...")
    generate_all_plots()

    elapsed = time.time() - start_time
    print("======================================================================")
    print(f"  EXPERIMENT RUN COMPLETED SUCCESSFULLY in {elapsed:.2f} seconds!")
    print("======================================================================")

if __name__ == '__main__':
    main()
