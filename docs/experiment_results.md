# Experimental Results & Performance Analysis

## 1. Experimental Setup & Matrix

Experiments were executed across 3 network congestion scenarios over 5 independent random seeds ($3 \times 4 \times 5 = 60$ experiment runs, evaluating $60 \times 50 = 3,000$ flow instances).

### Evaluation Baselines & Methods
1. **FIFO + OSPF (Static Baseline):** Standard Open Shortest Path First routing along minimum hop-count links with First-In-First-Out switch buffer scheduling.
2. **PQ + OSPF (Priority Queuing Baseline):** OSPF routing combined with strict Priority Queuing at switch output buffers.
3. **Adaptive Prioritization + OSPF:** The paper's dynamic service category and SLA prioritization algorithm applied to queues, but retaining static OSPF shortest paths.
4. **Proposed Combined SOSDN Approach:** Joint execution of adaptive service prioritization, multi-criteria QoS-aware routing (Dijkstra over dynamic $W_{i,j}$ weights), and optimal SOA server selection based on additive utility $F(S_k)$.

---

## 2. Quantitative Summary Across Scenarios

The table below summarizes the aggregate performance metrics across all 50 flows (mean $\pm$ standard deviation) collected from `summary_metrics.csv`:

| Scenario | Routing & Queuing Method | Packet Loss (%) | Delay (ms) | Jitter (ms) | QoE Score (MOS) | Server CPU Load (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Low Congestion** | FIFO + OSPF | $0.68 \pm 0.54$ | $140.78 \pm 72.83$ | $0.76 \pm 0.26$ | $4.91 \pm 0.10$ | $71.62 \pm 20.01$ |
| | PQ + OSPF | $0.68 \pm 0.53$ | $139.76 \pm 72.88$ | $0.65 \pm 0.33$ | $4.92 \pm 0.09$ | $71.62 \pm 20.01$ |
| | Prioritization + OSPF | $0.68 \pm 0.53$ | $139.26 \pm 72.71$ | $0.61 \pm 0.34$ | $4.92 \pm 0.09$ | $71.62 \pm 20.01$ |
| | **Proposed Combined (SOSDN)** | **$0.28 \pm 0.11$** | **$97.48 \pm 36.09$** | **$0.60 \pm 0.35$** | **$4.99 \pm 0.00$** | **$61.58 \pm 9.00$** |
| **Medium Congestion** | FIFO + OSPF | $0.76 \pm 0.62$ | $144.42 \pm 75.64$ | $1.99 \pm 1.64$ | $4.87 \pm 0.15$ | $71.62 \pm 20.01$ |
| | PQ + OSPF | $0.73 \pm 0.59$ | $142.58 \pm 75.02$ | $1.56 \pm 1.18$ | $4.89 \pm 0.13$ | $71.62 \pm 20.01$ |
| | Prioritization + OSPF | $0.72 \pm 0.58$ | $141.75 \pm 74.56$ | $1.40 \pm 1.02$ | $4.90 \pm 0.12$ | $71.62 \pm 20.01$ |
| | **Proposed Combined (SOSDN)** | **$0.32 \pm 0.13$** | **$99.97 \pm 37.14$** | **$1.40 \pm 1.02$** | **$4.99 \pm 0.00$** | **$61.58 \pm 9.00$** |
| **High Congestion** | FIFO + OSPF | $1.80 \pm 1.44$ | $190.79 \pm 106.14$ | $24.66 \pm 20.35$ | $3.33 \pm 1.79$ | $71.62 \pm 20.01$ |
| | PQ + OSPF | $1.51 \pm 1.19$ | $179.04 \pm 98.78$ | $19.24 \pm 16.80$ | $3.43 \pm 1.77$ | $71.62 \pm 20.01$ |
| | Prioritization + OSPF | $1.35 \pm 1.03$ | $173.31 \pm 93.98$ | $16.85 \pm 15.31$ | $3.53 \pm 1.66$ | $71.62 \pm 20.01$ |
| | **Proposed Combined (SOSDN)** | **$0.88 \pm 0.66$** | **$129.85 \pm 56.04$** | **$14.40 \pm 13.67$** | **$4.28 \pm 1.14$** | **$61.58 \pm 9.00$** |

---

## 3. Bottleneck Analysis: User 7 Overload Scenario

User 7 represents an IPTV subscriber with strict SLA QoE requirement ($QoE \ge 4.0$, target 5.0) attached to edge switch `SW4_E1`. Under high congestion, User 7's direct path traverses the saturated core bottleneck link `SW4 -> SW1`.

The table below contrasts our empirical findings directly against the reference benchmark values reported in Beshley et al. (2024):

| Metric | FIFO + OSPF | PQ + OSPF | Prioritization + OSPF | Proposed Combined (SOSDN) | Paper Reference Benchmark (Beshley et al.) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Packet Loss Rate** | $4.45\%$ | $3.51\%$ | $1.93\%$ | **$0.93\%$** | *Reported: Loss drops below 1% for SOSDN* |
| **End-to-End Delay** | $361.81\text{ ms}$ | $324.45\text{ ms}$ | $257.22\text{ ms}$ | **$152.21\text{ ms}$** | *Reported: Significant reduction via detour* |
| **Jitter** | $55.97\text{ ms}$ | $41.98\text{ ms}$ | $16.79\text{ ms}$ | **$16.23\text{ ms}$** | *Reported: Jitter stabilized under threshold* |
| **Integral QoS ($x$)** | $0.852$ | $0.781$ | $0.512$ | **$0.218$** | *Paper Eq. (20): Drops from Red to Green* |
| **Alert Level** | Red Alert | Red Alert | Red Alert | **Yellow/Green Alert** | *Red Alert $\to$ High Quality* |
| **QoE Score (MOS)** | **$1.07$** | **$1.15$** | **$2.59$** | **$4.84$** | **PQ+OSPF: 1.9 $\to$ Proposed: 4.7** |

### Key Experimental Insights:
1. **Queuing Prioritization Alone Is Insufficient:** While Adaptive Prioritization reduces User 7's packet loss from $3.51\%$ to $1.93\%$ and raises QoE from $1.15$ to $2.59$, it remains trapped on the saturated `SW4 -> SW1` bottleneck. Without dynamic routing, queuing delays remain high ($257\text{ ms}$), triggering a Red Alert ($QoE < 3.0$).
2. **Multi-Criteria Detour Rerouting:** When multi-criteria link cost calculation activates, the link weight of `SW4 -> SW1` surges to $W_{4,1} \approx 0.98$. The Dijkstra multi-criteria engine offloads User 7 via `SW4 -> SW2 -> SW1` ($W \approx 0.79$), slashing queuing delay to $152.2\text{ ms}$ and loss to $0.93\%$.
3. **Server Load Balancing:** Static assignment pinned requests to overloaded IPTV Server 2 ($71.6\%$ CPU). The additive utility function dynamically redirects traffic to IPTV Server 1, reducing peak server load to $61.6\%$ and eliminating server-side queuing delays.
4. **QoE SLA Satisfaction:** Under SOSDN, User 7 achieves a QoE score of **$4.84$**, fully satisfying the service-level agreement ($QoE \ge 4.0$).
