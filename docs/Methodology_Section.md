# Chapter 3: Methodology

## 3.1 Research Design
This study employs a quantitative, experimental systems design approach to formulate, implement, and evaluate the "Autonomous AI Bot for Self-Healing and Proactive Server Health Management." The research methodology centers on simulating a distributed, microservices-oriented architecture that inherently exhibits common administrative and networking vulnerabilities. By designing this controlled environment, the proposed AI-driven anomaly detection and mitigation strategies can be empirically validated. This research transitions the paradigm of server infrastructure management from reactive, human-dependent administration to an autonomous, closed-loop self-correcting system. The experimental design strictly controls attack vectors while systematically observing key performance indicators, including response latency, detection accuracy, and the success rate of autonomous healing interventions, comparing these against established manual operational baselines.

## 3.2 System Architecture
The proposed system architecture establishes a resilient, closed-loop mechanism comprising five primary, interconnected layers designed for continuous monitoring and rapid fault resolution:

1. **Data Collection Layer:** Operating as the sensory foundation of the architecture, this layer utilizes monitoring agents distributed across the infrastructure. It continuously aggregates high-fidelity telemetry concerning resource utilization and network packet flows.
2. **AI-Driven Threat Detection Layer:** Functioning as the primary analytical engine, this component ingests normalized data streams to distinguish benign workloads from malicious anomalies, specifically Distributed Denial of Service (DDoS) patterns, utilizing an eXtreme Gradient Boosting (XGBoost) classification model.
3. **Reinforcement Learning (RL) Decision Module:** Acting as the strategic optimizer, this module evaluates the current state of the degraded system and queries its learned policy to select the most statistically optimal mitigation strategy.
4. **Autonomous Healing Engine:** Serving as the operational actuator, this engine executes the specific remediation workflows dictated by the RL module autonomously, interfacing securely with the application host.
5. **Distributed Deployment Environment:** Providing the foundational infrastructure, this layer consists of containerized microservices hosted within Docker, ensuring that realistic network topology and resource constraints are maintained to guarantee simulation fidelity.

## 3.3 Data Acquisition and Preprocessing
High-fidelity data acquisition is requisite for the calibration and accuracy of the machine learning models. The data collection layer continuously ingests two concurrent streams of system information:

- **Continuous System Telemetry:** Distributed monitoring agents (developed in Python utilizing the `psutil` library) collect high-frequency time-series data at 60-second intervals. These metrics encompass CPU utilization, memory consumption, disk I/O, active network connection thresholds, and application-level HTTP error rates.
- **Network Traffic Metadata:** To facilitate precise DDoS detection, comprehensive flow-based metrics—such as forward-to-backward packet ratios, flow durations, and inter-arrival times (IAT)—are intercepted and aggregated.

For foundational model training, the CIC-DDoS2019 dataset was integrated to provide a robust corpus of labeled benign and malicious traffic matrices, intrinsically grounding the detection architecture in empirically validated attack vectors. Following ingestion, raw telemetry undergoes systematic preprocessing. Continuous features undergo feature scaling utilizing a unit-variance transformation (`StandardScaler`), ensuring all inputs manifest a mean of zero and a standard deviation of one. This standardization prevents features with inherently high magnitudes from disproportionately biasing the decision boundaries of the classification models. Furthermore, time-windowed aggregations (e.g., rolling averages and trend slopes) are engineered to identify progressive resource exhaustion patterns.

## 3.4 Threat Detection Implementation
The core threat detection mechanism leverages an XGBoost classifier, selected for its proven efficacy and computational efficiency in analyzing structured, tabular network datasets. The XGBoost algorithm employs a gradient boosting framework, systematically constructing an ensemble of decision trees to minimize classification error. 

The hyperparameter configuration defines an ensemble of 100 to 200 estimators with constrained maximum depths (typically 6 to 8) to mitigate the risk of overfitting the training distribution. The algorithm's learning rate is optimized to sequentially minimize binary cross-entropy across training iterations. During active inference, the model evaluates incoming, normalized multi-dimensional feature vectors to output a localized probability score denoting the likelihood of malicious traffic. 

To formalize the anomaly detection mechanism, the classification function $A(x)$ is defined as:

$$
A(x) = \begin{cases} 
1 & \text{if } P(x) > \theta \\
0 & \text{otherwise}
\end{cases}
$$

**Where:**
- $x$ = network feature vector
- $P(x)$ = predicted attack probability from the XGBoost model ($0.0 \le P(x) \le 1.0$)
- $\theta$ = empirically derived detection threshold ($\theta = 0.85$)

Traffic segments where $A(x) = 1$ are classified as active DDoS threats, immediately triggering the mitigation pipeline.

## 3.5 Reinforcement Learning Optimization and Autonomous Healing (Strategic Roadmap)
To address the inherent dynamism of distributed infrastructures, a Reinforcement Learning (RL) framework is designated as the strategic optimizer for the selection of subsequent healing interventions. Currently, in the v1.0 deployment, the healing orchestrator utilizes a robust **rule-based expert system** to map specific identified fault states to deterministic mitigation scripts (e.g., executing `systemctl restart` for failed background services, or `docker restart` for container crashes). This provides immediate, reliable fault resolution.

However, the architecture is designed to transition to a Markov Decision Process (MDP) RL model in future iterations. The planned RL framework characterizes the environment as:

- **State Space ($S$):** The quantitative health profile of the server matrix, defined by CPU/Memory loads, request error rates, and the active DDoS prediction confidence score.
- **Action Space ($A$):** The discrete set of permissible mitigation strategies, including implementing `iptables` rules for traffic dropping, initiating controlled service restarts, allocating additional Docker container replicas, or redirecting traffic loads.
- **Reward Function ($R$):** The evaluative feedback mechanism driving the RL agent's policy. The reward is formulated to maximize swift system recovery and metric stability while heavily penalizing false-positive mitigations (e.g., dropping legitimate user traffic) or the inadvertent triggering of cascading subsystem failures. 

Formally, the optimization objective is to maximize the expected cumulative reward, governed by the Q-learning update rule:

$$
Q(S_t, A_t) \leftarrow Q(S_t, A_t) + \alpha \left[ R_{t+1} + \gamma \max_a Q(S_{t+1}, a) - Q(S_t, A_t) \right]
$$

**Where:**
- $S_t, S_{t+1}$ = current and subsequent states
- $A_t$ = action taken at time $t$
- $R_{t+1}$ = reward received after taking action $A_t$
- $\alpha$ = learning rate ($0 < \alpha \le 1$)
- $\gamma$ = discount factor ($0 \le \gamma < 1$)

While the current operational logic executes rule-based remediation via the Autonomous Healing Engine, this engine continuously logs state-action-reward tuples into the `HealingHistory` database. This live operational data serves as the foundational training environment for the offline pre-training of the RL policy network, ensuring safe exploration prior to deploying the RL agent in active production.

## 3.6 Implementation Pipeline and Algorithmic Workflow
The unified detection and autonomous healing process follows a continuous, closed-loop algorithmic sequence operating within a Docker-based microservices environment. 

The operational pipeline initiates with the continuous parsing and stabilization of incoming metric streams ($\mathbf{x}_t$). The XGBoost classifier assesses these vectors ($\hat{y}_t = \text{XGBoost}(\mathbf{x}_t)$). Upon surpassing the threat threshold, an asynchronous alert is generated, prompting the RL Decision Module to construct the current state matrix ($S_t$). The trained RL policy network evaluates $S_t$ to yield the optimal mitigation action ($A_t$), which the Autonomous Engine immediately executes via the Docker daemon or host OS firewall. 

Following a designated stabilization and verification window (e.g., 300 seconds), system metrics are continuously re-evaluated. If the metrics reflect an expedited return to the baseline state ($S_{t+1}$), a positive Reward ($R_t$) is computed, and the RL policy is iteratively updated to reinforce the successful action pair. If the degradation persists, the architecture autonomously escalates to a more aggressive structural mitigation action.
