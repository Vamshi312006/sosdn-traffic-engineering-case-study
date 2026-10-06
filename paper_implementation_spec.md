# Technical Specification & Paper Extraction
## "Traffic Engineering and QoS/QoE Supporting Techniques for Emerging Service-Oriented Software-Defined Network"

**Citation:**  
Mykola Beshley, Natalia Kryvinska, Halyna Beshley, Oleksiy Panchenko, and Mykhailo Medvetskyi,  
*"Traffic Engineering and QoS/QoE Supporting Techniques for Emerging Service-Oriented Software-Defined Network"*,  
**Journal of Communications and Networks**, Vol. 26, No. 1, pp. 99–114, February 2024.  
**DOI:** [10.23919/JCN.2023.000065](https://doi.org/10.23919/JCN.2023.000065)

---

### A. Architecture

#### 1. SOSDN Architecture Overview
The Service-Oriented Software-Defined Network (SOSDN) proposed by Beshley et al. integrates Software-Defined Networking (SDN) with Service-Oriented Architecture (SOA) to deliver coordinated, end-to-end Quality of Service (QoS) and Quality of Experience (QoE). Traditional networks separate network routing from application/compute server management; SOSDN centralizes both domains under an SDN control plane cooperating with a service orchestrator.

#### 2. Planes and Roles
As defined in Section III (Figs. 1 & 2):
1. **Management, Monitoring, and Adaptation Level (Infrastructure Layer):**
   - **SDN Switches (Network Domain):** Forward data packets according to OpenFlow rules; collect port-level counters and traffic statistics.
   - **SOA Service Servers (Computing Domain):** Run application microservices (VoIP, IPTV, VoD, Web); host local monitoring agents collecting compute metrics.
2. **SDN Controller (Control Plane):**
   - Central programmable entity managing flow tables across all 16 switches.
   - Hosts the *Adaptive Service Prioritization Algorithm*, *Adaptive Multi-Criteria Routing Method*, and *Adaptive Criterion Weighting Controller*.
   - Coordinates with the Service Orchestrator to exchange network path state and server placement/selection state.
3. **Service Orchestrator & Server Resource Controller:**
   - Monitors physical and virtual computing resources (CPU, RAM, response latency, drop rates).
   - Executes the *Multi-Criteria Service Server Selection Algorithm* based on an integral additive criterion.
   - Sends chosen optimal server information to the SDN controller so paths can be constructed accordingly; receives triggers from the SDN controller when QoS degrades.
4. **User-Centric QoE Agreement (Application Layer / User Cabinet):**
   - End users establish SLA contracts with QoE scores rated from 1 to 5.
   - The network dynamically reconfigures its resource allocations to maintain user SLA commitments.

#### 3. Mathematical Conditions for End-to-End QoS (Formulas 1–4)
To ensure end-to-end QoS from user device to service server:
$$\text{QoS}_{E2E}(x) \le \text{QoS}_{E2E.admissible}(x) \quad \text{--- (1)}$$

Where $\text{QoS}_{E2E.admissible}(x)$ is the acceptable value under the SLA contract, composed of allowable allocations across both domains:
$$\text{QoS}_{E2E}(x) = \text{QoS}_{Network}(x) + \text{QoS}_{Server}(x) \quad \text{--- (2)}$$

Subject to independent domain admissibility constraints:
$$\text{QoS}_{Network}(x) \le \text{QoS}_{N.admissible}(x) \quad \text{--- (3)}$$
$$\text{QoS}_{Server}(x) \le \text{QoS}_{S.admissible}(x) \quad \text{--- (4)}$$

Where $x$ represents delay, packet loss, jitter, or a complex integral index. If one domain experiences overload or burstiness (e.g., self-similar traffic bursts), the controller can compensate by optimizing the other domain (e.g., re-routing around network congestion or selecting a lighter server).

---

### B. Network Topology & Experimental Environment

#### 1. Paper Testbed Specification (Section VII, Fig. 9a & 9b)
- **Host Hardware:** 11th Gen Intel(R) Core(TM) i5-1165G7 @ 2.50 GHz, 8.0 GB RAM (7.7 GB usable), Windows 11 host OS.
- **Virtualization:** Oracle VirtualBox 7.0 running Ubuntu Linux 20.04.5 LTS (4 vCPUs, 6222 MB RAM).
- **SDN Stack:** Mininet 2.2.1 extended with **Containernet**; OpenDaylight controller; Java-based custom control applications.
- **Topology Structure (Fig. 9b):**
  - **16 SDN Switches:**
    - 4 Core switches ($SW1, SW2, SW3, SW4$) connected in a full mesh ($K_4$ core: SW1-SW2, SW2-SW3, SW3-SW4, SW4-SW1, SW1-SW3, SW4-SW2).
    - 12 Edge/access switches grouped in clusters of 3 attached to each core switch ($4 \times 3 = 12$).
  - **Link Bandwidth:** 100 Mbit/s on all emulated links.
  - **6 SOA Servers:** Deployed in Docker containers:
    - *IPTV Server 1* (attached to SW1 domain)
    - *IPTV Server 2* (attached to SW1 domain, artificially loaded heavier than Server 1)
    - *VoIP Server* (attached to SW1 domain)
    - *Web Server* (attached to SW4 domain)
    - *VOD Server* (Media on Demand, attached to SW4 domain)
    - Replicated server instance
  - **50 Users Total:** Distributed across the edge switches.

#### 2. Service-User Distribution & Typographical Inconsistency
The paper states on Page 12 (Section VII):
> *"The developed network is designed for 50 users and will allow to provide them with a good level of such services as VoIP, IPTV, Internet data, Media on Demand. Users use all 4 presented services in this proportion 10 VOIP users, 20 IPTV users, 10 Internet data users and 10 IPTV users."*

- **Exact Paper Wording:** `"10 VOIP users, 20 IPTV users, 10 Internet data users and 10 IPTV users"`
- **Analysis:**
  - The text introduces exactly 4 services: VoIP, IPTV, Internet data, Media on Demand (VoD).
  - The listed counts sum to: $10 + 20 + 10 + 10 = 50$ users.
  - The second occurrence of `"10 IPTV users"` is a clear typographical error for **10 Media on Demand (VoD) users**.
  - This is corroborated by Fig. 9b, which explicitly shows the `VOD` server alongside `WEB`, `VOIP`, and `IPTV Server 1 & 2`.
  - Among the IPTV users, **10 specific users** have an individual SLA QoE target score of 5. User 7 is the highlighted test subject whose QoS deteriorates under baseline conditions.

#### 3. Traffic Generation Details
- **VoIP:** Synthetic traffic generated via `iPerf` over UDP using G.711 (64 kbit/s) and G.729 codecs.
- **IPTV:** Real video streaming of a prepared 60-second 720p H.264 video file; users require $\ge 2$ Mbit/s bandwidth.
- **Web / Internet Data:** HTTP request flows.
- **Media on Demand (VoD):** Stored video streams.

---

### C. Network & Server Monitoring Metrics

#### 1. Network Domain (SDN Controller & OpenFlow / sFlow)
- **Packet Loss ($P$ / $p$):** Measured as percentage ratio $\frac{N_{loss}}{M_{sent}} \times 100\%$.
- **Packet Delay ($T$ / $t$):** End-to-end packet transmission delay in milliseconds (ms).
- **Jitter ($J$ / $j$):** Packet delay variation in milliseconds (ms).
- **Available Bandwidth ($C$ / $c$):** Residual link throughput in Mbit/s or kbit/s.

#### 2. Server Domain (sFlow Collector & Server Agents)
- **CPU Loading (%):** Percentage utilization of the host/container processor.
- **RAM Loading (%):** Memory consumption percentage.
- **Average Request Processing Time (ms):** Mean server-side response delay.
- **Probability of Losing Requests (%):** Ratio of dropped/rejected requests to total incoming requests.
- **Network Interface Loading (%):** Utilization percentage of the server NIC.

---

### D. Adaptive Service Prioritization Algorithm

#### 1. Service Classes & QoS Requirements (Table I)

| Flow Type ($i$) | Service Description | Loss $P$ (%) | Delay $T$ (ms) | Jitter $J$ (ms) | Bandwidth $C$ (kbit/s) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **A** | Real-time voice data (VoIP), automated IoT emergency calls | $< 0.25$ | 150 | 10 | 64 |
| **B** | Video conferencing, distance learning, IoT real-time monitoring | $< 2$ | 100 | 20 | 2048 |
| **C** | Real-time video, IPTV, IoVT | $< 1$ | 100 | 50 | 4096 |
| **D** | Internet data (HTTP, online services), IoT notifications | $< 0.1$ | 100 | 100 | 2048 |
| **E** | Video on demand (VoD), IoVT surveillance | $< 0.1$ | 400 | 30 | 2048 |
| **F** | 720p non-real-time video | $< 1$ | 400 | 500 | 4000–10000 |

#### 2. Normalization of Relative QoS Parameters (Formulas 5–8)
Relative coefficients compare current measured values to the ideal minimum reference:
- Relative packet loss ratio:
  $$p = \frac{P_{min}}{P} \quad \text{--- (5)}$$
- Relative packet delay ratio:
  $$t = \frac{T_{min}}{T} \quad \text{--- (6)}$$
- Relative jitter ratio:
  $$j = \frac{J_{min}}{J} \quad \text{--- (7)}$$
- Relative bandwidth ratio:
  $$c = \frac{C}{C_{max}} \quad \text{--- (8)}$$

#### 3. Parameter Significance & Expert Weights (Table II)
- Significance values $Y_{ij} \in \{1, 2, 3\}$ correspond to low, medium, and high importance:

| Flow Type ($i$) | $P$ (Loss) | $T$ (Delay) | $J$ (Jitter) | $C$ (Bandwidth) |
| :---: | :---: | :---: | :---: | :---: |
| **A** | 2 | 3 | 3 | 1 |
| **B** | 2 | 3 | 3 | 2 |
| **C** | 3 | 2 | 2 | 3 |
| **D** | 3 | 1 | 1 | 1 |
| **E** | 2 | 2 | 1 | 1 |
| **F** | *Paper Typo* [1] | *Paper Typo* [400] | *Paper Typo* [500] | *Paper Typo* [4000–10000] |

> **Documented Typo in Table II:** In the original paper, Row F in Table II was accidentally pasted with the numerical requirements from Table I (`<1`, `400`, `500`, `4000–10000`) instead of discrete significance scores in $\{1, 2, 3\}$. The logical significance for 720p non-real-time video is Loss: 2, Delay: 1, Jitter: 1, Bandwidth: 3.

- **Global Parameter Weights ($Z_j$):**
  - Packet loss significance: $P_p = 0.23$
  - Delay significance: $P_t = 0.18$
  - Jitter significance: $P_j = 0.14$
  - Bandwidth significance: $P_c = 0.12$
  *(Note: unnormalized sum is 0.67; normalized weights are $0.343, 0.269, 0.209, 0.179$)*

#### 4. Relative Priority Calculation (Formula 9)
$$Pr_i = \frac{\sum_{j=1}^4 X_{ij} Y_{ij} Z_j}{\sum_{i=1}^6 \sum_{j=1}^4 X_{ij} Y_{ij} Z_j} \quad \text{--- (9)}$$
Where:
- $Pr_i \in [0, 1]$ is the relative priority of service flow $i$.
- $X_{ij}$ is the relative priority of parameter $j$ for service $i$ (derived from normalized monitored parameters or SLA tier).
- $Y_{ij}$ is the importance of parameter $j$ for service $i$.
- $Z_j$ is the global significance coefficient of parameter $j$.

#### 5. Priority Categories & SDN Enforcement (Fig. 3 & Fig. 4)
Calculated priorities are sorted, encoded into DSCP / ToS headers (starting with binary `001`, using top 2 bits for critical override), and grouped into three operational categories:
1. **Category 1 (Delay/Jitter Sensitive, e.g., VoIP):** Must be transmitted on a single optimal path. Multipath splitting and re-routing load balancing are strictly forbidden to prevent jitter.
2. **Category 2 (Loss Sensitive, e.g., IPTV, Video Streaming):** Can be balanced across a small set of alternative disjoint paths with low splitting ratio.
3. **Category 3 (Best Effort / Non-sensitive, e.g., Web, Background Data):** Can be redirected freely onto lightly loaded links to offload congested core paths.

---

### E. Adaptive Multi-Criteria Routing Method

#### 1. Link Criteria Normalization (Formulas 12–15)
For each directed link $(i, j)$ in adjacency matrix $A$:
- Packet loss: $P_{i,j} = \frac{N_{i,j}}{M_{i,j}}$ where $N_{i,j}$ is received packets and $M_{i,j}$ transmitted packets. (Alternatively, normalized as $P_{i,j} = \frac{P_{min}}{P_{i,j}}$).
- Delay: $D_{i,j} = \frac{t_{min}}{t_{i,j}}$ where $t_{min} = \min_{(u,v)} t_{u,v}$.
- Available bandwidth: $C_{i,j} = \frac{B_{i,j}}{B_{max}}$ where $B_{max} = \max_{(u,v)} B_{u,v}$.
- Jitter: $J_{i,j} = \frac{jt_{min}}{jt_{i,j}}$ where $jt_{min} = \min_{(u,v)} jt_{u,v}$.

#### 2. Integral Link Cost Metric (Formula 16)
$$W_{i,j} = 1 - \Big( X_1 \cdot P_{i,j} + X_2 \cdot D_{i,j} + X_3 \cdot C_{i,j} + X_4 \cdot J_{i,j} \Big) \quad \text{--- (16)}$$
Where $X_1, X_2, X_3, X_4$ are criterion weight coefficients satisfying:
$$\sum_{k=1}^4 X_k = 1, \quad 0 \le X_k \le 1 \quad \text{--- (18)}$$

#### 3. Path Selection & Objective Function (Formula 17)
$$F(\text{path}) = \sum_{(i,j) \in \text{path}} W_{i,j} \to \min \quad \text{--- (17)}$$
A path with lower accumulated link metric $W_{i,j}$ represents higher normalized performance (lower loss, lower delay, higher bandwidth, lower jitter).

#### 4. Load Balancing & Flow Re-allocation Order (Fig. 4)
When link/port congestion is detected:
1. Identify all flows on the congested interface.
2. Sort flows by category in ascending order of priority.
3. **First offload Category 3 flows** (Web/data) to alternative paths.
4. If congestion persists, balance **Category 2 flows** (IPTV) across qualified alternative paths.
5. **Protect Category 1 flows** (VoIP); do not split.
6. Re-evaluate QoS; stop redistribution once all streams meet SLA.

---

### F. Multi-Criteria Optimal Server Selection

#### 1. Server Criteria & Normalization (Table III, Formula 19)
The Orchestrator evaluates candidate servers across 5 partial criteria:
1. CPU loading ($i=1$): $\alpha_1 = 0.3$, best minimum $f_1^0 = 50\%$
2. RAM loading ($i=2$): $\alpha_2 = 0.2$, best minimum $f_2^0 = 30\%$
3. Average request processing time ($i=3$): $\alpha_3 = 0.2$, best minimum $f_3^0 = 100$ ms
4. Probability of losing requests ($i=4$): $\alpha_4 = 0.2$, best minimum $f_4^0 = 0.3\%$
5. Network interface loading ($i=5$): $\alpha_5 = 0.1$, best minimum $f_5^0 = 60\%$

Sum of weights: $\sum_{i=1}^5 \alpha_i = 0.3 + 0.2 + 0.2 + 0.2 + 0.1 = 1.0$.

#### 2. Utility Additive Function
$$F(x) = \sum_{i=1}^5 \alpha_i \frac{f_i^0(x)}{f_i(x)} \to \max \quad \text{--- (19)}$$

#### 3. Author Evaluation Example (Azure 3-Server Case)
- **Server 1:** $F(x) = 0.3(\frac{50}{60}) + 0.2(\frac{30}{50}) + 0.2(\frac{100}{100}) + 0.2(\frac{0.3}{0.3}) + 0.1(\frac{60}{80}) = 0.845$
- **Server 2:** $F(x) = 0.3(\frac{50}{70}) + 0.2(\frac{30}{30}) + 0.2(\frac{100}{150}) + 0.2(\frac{0.3}{0.8}) + 0.1(\frac{60}{70}) = 0.707$
- **Server 3:** $F(x) = 0.3(\frac{50}{50}) + 0.2(\frac{30}{60}) + 0.2(\frac{100}{400}) + 0.2(\frac{0.3}{0.3}) + 0.1(\frac{60}{60}) = 0.750$
- **Result:** Server 1 has the maximum utility ($0.845$) and is selected.

---

### G. QoE Model & QoS-to-QoE Mapping

#### 1. Integral Additive QoS Criterion for Live Video (Formula 20)
$$QoS(x) = 1 - \left( K_1 \frac{P_{min}}{P} + K_2 \frac{T_{min}}{T} + K_3 \frac{C}{C_{max}} + K_4 \frac{J_{min}}{J} \right) \quad \text{--- (20)}$$
Where $K_1 + K_2 + K_3 + K_4 = 1$. Lower $QoS(x)$ indicates closer adherence to ideal minimums.

#### 2. Non-Linear QoE Formulation (Formula 21)
The paper models user satisfaction on a 1–5 MOS scale as:
$$QoE(y) = 5 \times (1 - QoS^2(x))^{2.1} \cdot \sqrt[5]{QoS^8(x)} \quad \text{--- (21 text)}$$

*Note on Formula (21) vs. Fig. 11:*
- In Fig. 11, the empirical QoE curve decreases monotonically with $QoS(x)$ from $QoE \approx 4.95$ at $QoS(x)=0.1$ down to $QoE \approx 0.05$ at $QoS(x)=0.65$.
- Specifically, the paper marks:
  - $QoS = 0.17 \implies QoE = 4.7$ (Proposed adaptive routing + prioritization)
  - $QoS = 0.303 \implies QoE = 3.73$ (Proposed prioritization + OSPF)
  - $QoS = 0.41 \implies QoE = 1.9$ (PQ + OSPF)
  - $QoS = 0.50 \implies QoE = 0.7$ (FIFO + OSPF)

#### 3. Expert Assessment Ranges (Tables IV & V)

**Table IV: QoS vs User Satisfaction & QoE Score**
| Parameter | Good (QoE 4–5) | Fair (QoE 3.5–4) | Bad (QoE < 3.5) |
| :--- | :---: | :---: | :---: |
| **Delay ($T$)** | $< 150$ ms | 150–200 ms | $> 200$ ms |
| **Jitter ($J$)** | 0–20 ms | 20–50 ms | $> 50$ ms |
| **Packet Loss ($P$)** | 0–1% | 1–2% | $> 2%$ |
| **Bandwidth ($C$)** | $> 2$ Mbit/s | 1–2 Mbit/s | $< 1$ Mbit/s |

**Table V: Routing Path Metric vs QoE**
| QoE Estimation | Path Cost (Routing Metric) |
| :--- | :---: |
| **5 – 4** | $< 0.28$ |
| **3.5 – 4** | 0.28 – 0.32 |
| **$< 3.5$** | $> 0.35$ |

---

### H. Baselines & Comparison Methods

1. **FIFO + OSPF:** Standard single-shortest-path routing with first-in, first-out queuing on switches. No differentiation, no QoS awareness.
2. **PQ + OSPF:** Static priority queuing (RFC-based QoS classes) combined with static shortest path routing (OSPF). Flows receive fixed queuing priority, but routing ignores multi-parameter link load.
3. **Proposed Adaptive Prioritization + OSPF:** Dynamic prioritization (Formula 9) adjusting flow priority on switches, but still routing over standard OSPF shortest paths.
4. **Proposed Combined SOSDN Approach:** Coordinated Adaptive Prioritization + Adaptive Multi-Criteria Routing (Formula 16) + Optimal Server Selection (Formula 19).

---

### I. Original Paper Reported Results (Reference Benchmarks)
*(These numbers are recorded strictly as the paper's findings, NOT our experimental outputs)*

- **Baseline Overload (PQ + OSPF):**
  - IPTV User 7 packet loss: $\approx 1.9\%$ (Red zone)
  - IPTV User 7 delay: $\approx 275$ ms (Red zone)
  - IPTV User 7 jitter: $\approx 56$ ms (Red zone)
  - Resulting QoE: **1.9** (Bad perception)
- **Proposed Combined Method (SOSDN):**
  - IPTV User 7 packet loss: $\approx 1.05\%$ (Yellow zone, compliant with acceptable bounds)
  - IPTV User 7 delay: $\approx 200$ ms
  - IPTV User 7 jitter: $\approx 52$ ms
  - Resulting QoE: **4.7** (High satisfaction)
- **Component Breakdown (Fig. 11):**
  - FIFO + OSPF: $QoS = 0.50$, $QoE \approx 0.7$
  - PQ + OSPF: $QoS = 0.41$, $QoE = 1.9$
  - Prioritization + OSPF: $QoS = 0.303$, $QoE = 3.73$
  - Prioritization + Multi-Criteria Routing: $QoS = 0.17$, $QoE = 4.7$
