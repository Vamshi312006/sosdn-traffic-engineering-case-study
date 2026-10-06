# Service-Oriented Software-Defined Network (SOSDN) Simulation

## Computer Networks Case Study (Group 3)
**Topic Area:** SDN, NFV & Machine Learning  
**Reference Paper:**  
> Mykola Beshley, Natalia Kryvinska, Halyna Beshley, Oleksiy Panchenko, and Mykhailo Medvetskyi, *"Traffic Engineering and QoS/QoE Supporting Techniques for Emerging Service-Oriented Software-Defined Network,"* **Journal of Communications and Networks**, Vol. 26, No. 1, pp. 99–114, Feb. 2024. DOI: [10.23919/JCN.2023.000065](https://doi.org/10.23919/JCN.2023.000065).

---

## 1. Project Overview

This repository provides a genuine, reproducible, student-scale implementation of the traffic engineering, multi-criteria routing, adaptive service prioritization, and server selection mechanisms proposed by Beshley et al. (2024).

The system models:
- **16-Switch Topology:** 4 mesh core switches ($K_4$) connected to 12 edge switches via $100\text{ Mbit/s}$ links.
- **50 Multi-Service Users:** 20 IPTV users (Users 1–10 with strict QoE SLA requirement = 5.0), 10 VoIP users, 10 Web data users, and 10 Media on Demand (VoD) users.
- **6 SOA Servers:** 2 IPTV, 2 VoIP, 1 Web, 1 VoD servers evaluated via multi-criteria additive utility.
- **Experimental Matrices:** Evaluates 4 network control strategies across Low, Medium, and High network congestion scenarios over 5 random seeds ($3 \times 4 \times 5 = 60$ trials, $3,000$ flow evaluations).
- **Core Baselines Evaluated:**
  1. `FIFO + OSPF`: Static shortest-path routing with First-In-First-Out queuing.
  2. `PQ + OSPF`: Shortest-path routing with strict Priority Queuing.
  3. `Adaptive Prioritization + OSPF`: Dynamic service category/SLA priority calculation on static paths.
  4. `Proposed Combined SOSDN`: Joint adaptive prioritization, Dijkstra multi-criteria detour routing, and optimal server selection.

---

## 2. Directory Structure

```text
sosdn_case_study/
├── config/
│   └── experiment_config.yaml         # Topology, flow definitions, weights, and scenario configs
├── docs/
│   ├── implementation_notes.md        # Detailed formulas, architectural design, and paper differences
│   └── experiment_results.md          # Comprehensive numerical tables and performance analysis
├── results/
│   ├── figures/                       # Publication-grade evaluation figures
│   │   ├── fig1_qoe_by_scenario.png
│   │   ├── fig2_user7_overload_comparison.png
│   │   ├── fig3_iptv_qos_distribution.png
│   │   ├── fig4_qoe_growth_curve.png
│   │   └── fig5_server_load_comparison.png
│   ├── processed/                     # Aggregate metric CSVs
│   │   ├── summary_metrics.csv
│   │   └── user7_overload_summary.csv
│   └── raw/
│       └── results.csv                # 3,000 raw flow execution records
├── src/
│   ├── baselines.py                   # Orchestration of baseline and proposed algorithms
│   ├── experiment.py                  # Multi-scenario, multi-seed experiment runner
│   ├── monitoring.py                  # Queuing delay, buffer drops, and server load monitoring
│   ├── prioritization.py              # Formulas (5)-(9): Service and parameter priority calculation
│   ├── qos_qoe.py                     # Formulas (20): Integral QoS score and QoE mapping
│   ├── routing.py                     # Formulas (12)-(18): Link cost normalization & Dijkstra routing
│   ├── server_selection.py            # Formula (19): Multi-criteria server utility optimization
│   ├── topology.py                    # 16-switch NetworkX topology builder
│   ├── traffic.py                     # 50-user multi-service flow generator
│   └── visualization.py              # Matplotlib plotting scripts
├── tests/
│   ├── test_prioritization.py         # Priority calculation unit tests
│   ├── test_qoe.py                    # QoS-to-QoE mapping unit tests
│   ├── test_routing.py                # Multi-criteria routing unit tests
│   └── test_server_selection.py       # Server selection utility unit tests
├── paper_implementation_spec.md       # Full mathematical extraction from original paper
├── requirements.txt                   # Python dependencies
└── run_experiment.py                  # End-to-end execution script
```

---

## 3. Setup and Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- Required packages:
  ```bash
  pip install -r requirements.txt
  ```

### Running Unit Tests
All unit tests validate mathematical formulas against the paper's specification:
```bash
python -m unittest discover tests/
```

### Running the Full Experiment
To run all 60 experiment trials, compute summary statistics, and generate publication plots:
```bash
python run_experiment.py
```
Outputs are automatically written to `results/raw/`, `results/processed/`, and `results/figures/`.
