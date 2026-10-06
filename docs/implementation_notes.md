# Implementation Notes: Student-Scale SOSDN Architecture and Algorithms

## 1. Executive Summary & Purpose

This document details the engineering architecture, mathematical formulas, algorithmic workflows, and design decisions for our student-scale implementation of the Service-Oriented Software-Defined Networking (SOSDN) traffic engineering framework. 

The implementation is directly based on the research paper:
> **Mykola Beshley, Natalia Kryvinska, Halyna Beshley, Oleksiy Panchenko, and Mykhailo Medvetskyi**, *"Traffic Engineering and QoS/QoE Supporting Techniques for Emerging Service-Oriented Software-Defined Network,"* **Journal of Communications and Networks**, Vol. 26, No. 1, pp. 99–114, February 2024. DOI: 10.23919/JCN.2023.000065.

The core objective of this project is to implement a genuine, reproducible, and verifiable simulation of the paper's multi-criteria optimization algorithms, execute controlled experiments across varying network congestion regimes, collect empirical metrics, and evaluate how joint service prioritization, multi-criteria routing, and server selection improve end-to-end Quality of Experience (QoE) and Quality of Service (QoS).

---

## 2. Reproduction Scope and Differences from Original Paper

As established in our initial feasibility decision (Option B), the experimental environment is implemented as an analytical and discrete-event simulation model in Python rather than an exact reproduction of the authors' Java/OpenDaylight/Containernet Linux kernel testbed. Academic integrity requires full disclosure of these operational differences:

| Attribute | Original Paper (Beshley et al., 2024) | Group 3 Student-Scale Implementation | Rationale / Equivalence |
| :--- | :--- | :--- | :--- |
| **Execution Platform** | Linux, Mininet 2.2.1, Containernet, Docker | Windows Host, Python 3.14, NetworkX 3.4 | Reproducible on student workstation without Linux kernel container privileges. |
| **SDN Controller** | OpenDaylight (ODL) Controller via REST/OSGi | Centralized Controller class in Python | Models centralized topology graph, global state monitoring, and flow push. |
| **Switch Forwarding** | OpenFlow 1.3 switches in Mininet (OVS) | NetworkX directed graph routing tables | Flow paths and next-hop forwarding programmed identically via Dijkstra. |
| **Traffic Generation** | Real traffic + iPerf (UDP VoIP, H.264 720p video) | Synthetic flow generator with paper bitrates | Matches exact flow counts: 50 users (20 IPTV, 10 VoIP, 10 Web, 10 VoD). |
| **Queuing & Physics** | Linux `tc` netem queues (FIFO, PQ) | Analytical $M/M/1/B$ finite-buffer queuing model | Accurately reproduces non-linear queuing delay, jitter, and packet loss under load. |
| **Server Tier** | 6 Docker containers hosting SOA services | 6 simulated server endpoints with dynamic loads | Models CPU load, RAM load, request rate, and response processing time. |

---

## 3. Mathematical Formulation & Algorithmic Design

### 3.1 Adaptive Service Prioritization

The framework dynamically calculates relative service priorities across three categories:
- **Category 1 ($C_1$):** Guaranteed service quality (VoIP, IPTV with strict SLA).
- **Category 2 ($C_2$):** Adaptive service delivery (Media on Demand / VoD, adaptive streaming).
- **Category 3 ($C_3$):** Best-effort traffic (Web browsing, file downloads).

#### Formula (5): Service Category Factor
$$\xi_l = 1 - \frac{l - 1}{n}$$
Where $n = 3$ is the number of categories, and $l \in \{1, 2, 3\}$ is the service category index ($\xi_1 = 1.0, \xi_2 \approx 0.667, \xi_3 \approx 0.333$).

#### Formula (6): Parameter Importance Factor
$$\rho_{k, l} = 1 - \frac{k - 1}{m_l}$$
Where $m_l$ is the number of QoS parameters considered for category $l$, and $k$ is the parameter priority rank.

#### Formula (7): Relative Parameter Priority
$$P(q_{k, l}) = \frac{\xi_l \cdot \rho_{k, l}}{\sum_{l=1}^n \sum_{k=1}^{m_l} \xi_l \cdot \rho_{k, l}}$$
Subject to $\sum \sum P(q_{k, l}) = 1$.

#### Formula (8) & (9): User-Specific and Relative Priority
$$R_{s} = \sum_{k=1}^{m_l} P(q_{k, l}) \cdot \beta_{k, s}$$
$$\overline{P}_{s} = \frac{R_s}{\sum_{s=1}^S R_s}$$
Where $\beta_{k, s}$ represents user-specific SLA importance weights. Users with strict QoE contracts (such as IPTV Users 1–10 with SLA QoE requirement of 5.0) receive boosted priorities, protecting their packets from queue drops during congestion.

---

### 3.2 Adaptive Multi-Criteria Routing

Traditional OSPF routes traffic along the static shortest path (hop count), causing severe link bottlenecking and buffer overflows along core trunks. The SOSDN controller calculates dynamic link cost weights $W_{i,j}$ and computes optimal path detours using Dijkstra's algorithm.

#### Formula (12): Composite Link Weight Metric
$$W_{i,j} = \beta_{delay} \cdot \overline{T}_{i,j} + \beta_{loss} \cdot \overline{L}_{i,j} + \beta_{jitter} \cdot \overline{J}_{i,j} + \beta_{bw} \cdot \overline{B}_{i,j}$$
Subject to:
$$\sum_{p \in \{delay, loss, jitter, bw\}} \beta_p = 1, \quad \beta_p \ge 0$$
In our experimental configuration, standard weights are set to $\beta_{delay} = 0.3$, $\beta_{loss} = 0.3$, $\beta_{jitter} = 0.2$, and $\beta_{bw} = 0.2$.

#### Formulas (13)–(16): Dynamic Normalization
- **Normalized Delay:** $\overline{T}_{i,j} = \frac{T_{i,j} - T_{min}}{T_{max} - T_{min}}$
- **Normalized Packet Loss:** $\overline{L}_{i,j} = \frac{L_{i,j} - L_{min}}{L_{max} - L_{min}}$
- **Normalized Jitter:** $\overline{J}_{i,j} = \frac{J_{i,j} - J_{min}}{J_{max} - J_{min}}$
- **Normalized Bandwidth Utilization:** $\overline{B}_{i,j} = 1 - \frac{B_{avail, i,j}}{B_{capacity, i,j}} = \frac{B_{used, i,j}}{B_{capacity, i,j}}$

#### Congestion Detection and Detour Trigger
When a link experiences packet loss $L_{i,j} > 1.0\%$ or queuing delay exceeds threshold $\tau_{delay}$, the SDN controller triggers dynamic recalculation of link weights. Heavily congested direct links (e.g., `SW4 -> SW1` with $W_{SW4, SW1} \approx 0.98$) are penalized, prompting Dijkstra to route flows via lightly loaded two-hop detours (e.g., `SW4 -> SW2 -> SW1` with composite weight $\approx 0.79$).

---

### 3.3 Optimal Server Selection (SOA Tier)

Unlike static round-robin or nearest-server mapping, SOSDN evaluates SOA server health across 5 operational criteria using an integral additive utility function:

#### Formula (19): Server Utility Optimization
$$F(S_k) = \alpha_1 \cdot \overline{C}_{k} + \alpha_2 \cdot \overline{R}_{k} + \alpha_3 \cdot \overline{P}_{k} + \alpha_4 \cdot \overline{T}_{k}^{proc} + \alpha_5 \cdot \overline{I}_{k}$$
Where:
- $\overline{C}_k = 1 - \frac{CPU_k}{100}$ (Available CPU capacity)
- $\overline{R}_k = 1 - \frac{RAM_k}{100}$ (Available RAM capacity)
- $\overline{P}_k = 1 - P_{loss, k}^{req}$ (Probability of successful request processing)
- $\overline{T}_k^{proc} = 1 - \frac{T_k^{proc}}{T_{max}^{proc}}$ (Inverted normalized processing time)
- $\overline{I}_k = 1 - \frac{Load_{iface, k}}{BW_{iface, k}}$ (Available interface bandwidth)

Weight coefficients from Table III of the original paper:
$$\alpha = [0.30, 0.20, 0.20, 0.20, 0.10], \quad \sum_{m=1}^5 \alpha_m = 1.0$$
The controller assigns the flow to the server maximizing $F(S_k)$:
$$S_{optimal} = \arg\max_{S_k \in \mathcal{S}_{service}} F(S_k)$$

---

### 3.4 QoS-to-QoE Mapping Model

#### Formula (20): Integral Additive QoS Metric
$$x = \sum_{i=1}^M \omega_i \cdot \frac{|q_i - q_{i, \text{opt}}|}{|q_{i, \text{tol}} - q_{i, \text{opt}}|}$$
Where $q_i$ is the measured value of metric $i$, $q_{i, \text{opt}}$ is the ideal threshold, and $q_{i, \text{tol}}$ is the tolerable threshold. Parameter weights: $\omega_{loss} = 0.40, \omega_{delay} = 0.25, \omega_{jitter} = 0.20, \omega_{bw} = 0.15$.

#### QoE Quality Assessment & SLA Alert Mapping (Table V)
| Quality Level | Alert Level | Integral Score $x$ | QoE MOS Range | User Perception |
| :--- | :--- | :--- | :--- | :--- |
| **High** | Green Alert | $0.0 \le x < 0.2$ | $4.0 \le QoE \le 5.0$ | Imperceptible impairment, excellent quality. |
| **Medium** | Yellow Alert | $0.2 \le x < 0.5$ | $3.0 \le QoE < 4.0$ | Perceptible but acceptable impairment. |
| **Low** | Red Alert | $x \ge 0.5$ | $1.0 \le QoE < 3.0$ | Substantial distortion, unacceptable quality. |

---

## 4. Resolution of Paper Typographical Inconsistencies

During our technical review of the original PDF, three typographical errors in the paper were identified, documented, and handled:

1. **Table II (Importance Factor Row F):**
   - *Paper Text:* In row F, the authors accidentally copied the requirement boundary values from Table I (`<1, 400, 500, 4000-10000`) instead of discrete importance factors in $\{1, 2, 3\}$.
   - *Resolution:* Corrected to $[2, 1, 1, 3]$ matching the paper's ranking logic and verified in unit tests.
2. **Section VII Flow Distribution:**
   - *Paper Text:* States *"10 VOIP users, 20 IPTV users, 10 Internet data users and 10 IPTV users"* ($10+20+10+10 = 50$).
   - *Resolution:* The second mention of 10 IPTV users is a typographical error for 10 Media on Demand (VoD) users, as confirmed by Fig. 9(b) displaying the VoD server.
3. **Table III Server 1 Additive Utility Formulation:**
   - *Paper Text:* The printed text shows $0.2 \cdot (0.3/0.3)$ instead of $(0.3/0.5)$, but prints the resulting utility as $0.845$.
   - *Resolution:* Our unit test `test_server_selection.py` explicitly tests and validates the exact paper utility output ($0.845$).
