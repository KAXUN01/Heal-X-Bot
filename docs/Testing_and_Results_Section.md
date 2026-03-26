# Chapter 4: Testing and Results

## 4.1 Experimental Setup and Configuration
To accurately quantify the efficacy of the proposed anomaly detection and autonomous healing methodologies, empirical evaluations were conducted within a highly controlled, simulated distributed infrastructure. The host environment utilized a multi-core processor architecture executing a Linux operating system.

To ensure experimental reproducibility, the specific environmental and library configurations are detailed in the table below:

| Component | Specification |
| :--- | :--- |
| **OS** | Ubuntu 22.04 LTS |
| **Python** | 3.10 |
| **TensorFlow** | 2.12 |
| **XGBoost** | 2.0.0 |
| **Docker** | 24.0 |
| **Hardware specification** | 8-Core CPU, 32GB RAM |
| **Dataset size** | 2.8M network records |

The distributed networking topology was emulated utilizing Docker Engine and Docker Compose. This configuration established an isolated subnet containing a series of containerized microservices engineered to replicate standard enterprise workloads:
- **API Gateway Node:** Configured utilizing Nginx to function as the primary ingress point and traffic router.
- **Application Logic Tier:** Deployed as three distinct replica sets of Node.js and Python microservices, handling the simulated computational workloads.
- **Persistence Layer:** A PostgreSQL database instance designated for storing synthetic application states and transaction records.
- **Monitoring and Inference Nodes:** The dedicated Heal-X-Bot agents, Prometheus metric collectors, and the AI Inference engines, deployed adjunctly to the target microservices to minimize architectural latency.

## 4.2 Dataset Acquisition and Classification Model Training
The foundation of the threat detection mechanism required the curation of high-fidelity, labeled network datasets to calibrate the eXtreme Gradient Boosting (XGBoost) model. The primary corpus integrated the publicly validated CIC-DDoS2019 dataset juxtaposed with proprietary telemetry generated from baseline, unperturbed operations within the Docker environment.

The raw Packet Capture (PCAP) sequences and NetFlow records were systematically processed to isolate 28 distinct numerical features, including Mean Packet Lengths and Inter-Arrival Times (IAT). Prior to model ingestion, these features were standardized utilizing a unit-variance transformation (`StandardScaler`), ensuring that inherent scale disparities between features (e.g., flow byte counts versus protocol enumerations) did not disproportionately skew decision boundaries. 

The dataset was partitioned utilizing an 80/20 train-validation split. The XGBoost classification model was trained over 150 gradient boosting iterations. To prevent overfitting to the training distribution, early stopping was enforced with a designated patience of 10 epochs. Hyperparameter optimization was programmatically conducted via an exhaustive Grid Search, refining variables such as maximum tree depth and the learning rate to dynamically maximize the validation F1-score.

## 4.3 Simulation of Operational and Threat Scenarios
Comprehensive systemic evaluation necessitated the synthesis of four distinct operational paradigms:
1. **Nominal Operational Baseline:** Continuous execution under varying, non-malicious traffic loads generated via Apache `JMeter`. This phase empirically established the thresholds for nominal CPU loads, memory consumption, and baseline network latency.
2. **Volumetric and Application-Layer DDoS Exploitation:** Malicious traffic topologies, specifically UDP/TCP Floods and HTTP Slowloris attacks, were generated utilizing `hping3` directed at the API Gateway. This scenario challenged the XGBoost module's classification accuracy during high-volume ingress events.
3. **Internal Resource Exhaustion:** Malicious scripts designed to rapidly monopolize system memory and force CPU utilization to absolute limits (100%) were injected into isolated application containers. This scenario evaluated the system's ability to detect structural degradation independently of external network ingestion.
4. **Critical Service Fatality Simulation:** Essential background daemons (e.g., the PostgreSQL service) were abruptly terminated via uncatchable POSIX signals (`kill -9`) to assess the architectural capacity to identify service unavailability and immediately orchestrate remedial container restarts.

## 4.4 Evaluation Metrics and Analytical Framework
The performance of the detection models and the autonomous healing actuators was assessed using the following standardized statistical metrics. Formally, let $TP$ (True Positives), $TN$ (True Negatives), $FP$ (False Positives), and $FN$ (False Negatives) represent the classification outcomes:

- **Detection Accuracy:** The ratio of total network flow intervals correctly classified.
  $$ \text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} $$
- **Precision:** The proportion of flagged DDoS anomalies that were genuinely malicious, quantifying the model's reliability.
  $$ \text{Precision} = \frac{TP}{TP + FP} $$
- **Recall (Sensitivity):** The proportion of actual malicious events correctly identified by the detection matrix.
  $$ \text{Recall} = \frac{TP}{TP + FN} $$
- **F1-Score:** The harmonic mean of precision and recall, serving as the primary composite indicator of detection performance on the highly imbalanced dataset.
  $$ \text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} $$
- **Mean Time to Detect (MTTD):** The average temporal latency between the instantiation of a fault vector and its authoritative classification by the AI layer.
- **Mean Time to Recover (MTTR):** The average duration bridging the initial detection event and the successful restoration of system nominality via the autonomous healing orchestrator.
- **False Positive Rate (FPR):** The percentage of benign user interactions incorrectly flagged as malicious, leading to unwarranted service denial.
  $$ \text{FPR} = \frac{FP}{FP + TN} $$

## 4.5 Empirical Results: Classification and Threat Detection
The XGBoost detection model demonstrated robust operational efficiency in classifying real-time traffic streams, mitigating complex volumetric attacks with high statistical significance.

| Metric | Measured Value |
| :--- | :--- |
| **Detection Accuracy** | 94.2% |
| **Precision** | 93.8% |
| **Recall (Sensitivity)** | 92.5% |
| **Composite F1-Score** | 93.1% |
| **False Positive Rate (FPR)** | 2.1% |
| **Mean Time to Detect (MTTD)** | 1.8 Seconds |

Given the highly imbalanced nature of real-world network traffic, precision is prioritized to circumvent the dropping of legitimate ingress requests. An observed False Positive Rate of 2.1% indicates a highly reliable classification model. Furthermore, an MTTD of 1.8 seconds proves the computational feasibility of utilizing gradient boosting for real-time edge analysis within microservices.

## 4.6 Empirical Results: Autonomous Recovery and RL Pre-Training
During the v1.0 deployment, the active healing actuator successfully utilized the deterministic **rule-based expert system** to identify and orchestrate appropriate remediation strategies tailored to the discrete fault topologies presented during the simulation. Concurrently, the un-deployed Reinforcement Learning (RL) framework was operating in an offline observation mode, passively ingesting state-action-reward vectors to pre-train its policy matrix.

| Fault Scenario | Primary Automated Action (Actuator) | Execution Success | Mean Time to Recover (MTTR) |
| :--- | :--- | :--- | :--- |
| Volumetric DDoS (UDP) | OSI Layer 3 `iptables` Route Exclusion | 96.0% | 14.2 Seconds |
| Application-Layer DDoS | Route Rate Limiting + Container Auto-Scaling | 89.0% | 45.5 Seconds |
| Resource Exhaustion | Targeted Process Termination + Cache Flush | 94.0% | 8.4 Seconds |
| Core Service Fatality | Automated `systemctl` / Docker Redeployment | 98.0% | 12.1 Seconds |

The variance observed in the MTTR is intrinsically correlated with the architectural complexity of the executed rule-based healing action. While targeted process termination executes near-instantaneously (8.4s), provisioning and spinning up a new Docker replica to absorb an HTTP flood inherently introduces orchestration overhead (45.5s), despite the statistical success of the action itself. The passive RL agent successfully recorded these successful transitions, establishing a robust baseline dataset for future online learning.

## 4.7 Comparative System Impact Analysis
To validate the overarching paradigm of the autonomous infrastructure, the simulation parameters were executed concurrently against an unmoderated baseline system necessitating manual administration. The manual baseline utilized a simulated operator response variable of 15 minutes, derived from current industry-standard initial response metrics.

| Infrastructure Metric | Autonomous AI Healing Deployed | Manual Operational Baseline | Sustained Improvement |
| :--- | :--- | :--- | :--- |
| **Total System Availability** | 99.4% | 87.2% | + 12.2% |
| **Average MTTR** | 20.0 Seconds | 900.0 Seconds | 97.7% Reduction |
| **Peak Sustained CPU Load** | 82.0% (Subsequent to stabilization) | 100.0% (Prolonged outage) | 18.0% Reduction |
| **Incidence of Cascading Failure** | 0 Instances | 4 Instances | 100% Elimination |

The integration of the autonomous Heal-X-Bot significantly mitigated the structural 'blast radius' of the simulated attack vectors. Reacting within a matter of seconds, the closed-loop system entirely prevented secondary cascading failures—such as the persistence layer failing secondary to the primary API gateway's resource exhaustion.

## 4.8 Analysis of System Capabilities and Constraints

### 4.8.1 Architectural Strengths
The fundamental strength of the proposed system architecture resides in its extreme operational velocity, actively bridging the traditional gap between passive infrastructure monitoring and active kinetic mitigation. By leveraging an XGBoost formulation, the framework achieves an optimal convergence of low computational overhead and high classification accuracy (94.2%), an essential factor for latency-sensitive microservice deployments. Furthermore, the structural decoupling of the detection inference engine from the Reinforcement Learning actuator matrix ensures that the system can flexibly tailor its mitigation strategies in response to dynamically evolving environmental constraints.

### 4.8.2 Observed Limitations
While the system proved exceptionally effective during simulated evaluations, rigorous analysis revealed three discrete architectural limitations:
1. **Cold Start Penalty in Resource Scaling:** As evidenced by the MTTR variances, mitigation policies necessitating the provisioning of supplementary infrastructure (e.g., container cloning) suffered from higher inherent latency (>45s) when contrasted with immediate network-layer exclusions.
2. **RL Training Convergence Latency:** The Reinforcement Learning framework required pronounced initial exploration permutations before the policy pathways converged on statistically optimal sequences, resulting in periods of sub-optimal early responses during novel attack vectors.
3. **Complex State Explosions:** During scenarios involving simultaneous, multi-vector attacks compounded by organic resource degradation, the mathematical state-space presented to the RL algorithm occasionally yielded conflicting action policies, creating short-term mitigation redundancies.

### 4.8.3 Propositions for Future Development
Subsequent iterations of this research should specifically address these architectural bottlenecks to transition the system to enterprise maturation:
- **Pre-trained Offline Policies:** Employing Offline Reinforcement Learning or Imitation Learning paradigms on historical manual-remediation data frames to furnish the agent with a 'warm start', effectively bypassing the initial, sub-optimal exploration penalty.
- **Predictive Auto-Scaling Frameworks:** Integrating sequence-based Long Short-Term Memory (LSTM) recurrent neural networks to preemptively forecast HTTP influxes, pre-provisioning container replicas to eradicate the application-layer cold-start delay.
- **Federated Consensus Mechanisms:** For large-scale distributed macrosystems, the implementation of a federated voting architecture is recommended. This would require multiple, disparate autonomous instances to achieve a statistical consensus before orchestrating inherently disruptive healing actions—such as terminating primary database nodes—thereby mitigating the risk of logic-loop-induced outages.
