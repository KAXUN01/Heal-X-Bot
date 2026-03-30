# PRESENTATION SLIDES — 2nd Progress Evaluation
## Heal-X-Bot | Group 29 | BICT Honors Degree 2025

> **Note:** Each section below represents one presentation slide. Use these as content for your PowerPoint/Google Slides. The structure mirrors the provided template format.

---

---

## 📌 SLIDE 1 — Title Slide

**University of Sri Jayewardenepura**
**Faculty of Technology**

### AUTONOMOUS AI BOT FOR SELF-HEALING AND PROACTIVE SERVER HEALTH MANAGEMENT IN DISTRIBUTED SYSTEMS

**Heal-X-Bot**

Group 29 | BICT Honors Degree 2025

---

---

## 📌 SLIDE 2 — Project Reminder

| | |
|---|---|
| **Project** | Autonomous AI bot for self-healing and proactive server health management in distributed systems |
| **Reminder** | An AI-powered system that automatically detects DDoS attacks, blocks malicious IPs, monitors server health, and autonomously heals system failures — with explainable AI providing clear justifications for every action |

**Core Idea:**
- Uses ML-based DDoS detection to identify network threats in real-time
- **Predicts system failures 1–24 hours before they occur** using XGBoost
- Automatically blocks malicious IPs and restarts failed services
- Provides human-readable AI explanations for all automated decisions
- Deployed on Google Cloud Platform as a live, working system

---

---

## 📌 SLIDE 3 — Research Gap & Objectives

### Research Gap
> No existing integrated framework combines **(1) ML-based anomaly/DDoS detection**, **(2) autonomous self-healing**, and **(3) explainable AI** in a single system for distributed server environments.

### Research Objectives
1. Develop a TensorFlow-based ML model for real-time DDoS attack detection
2. Build an XGBoost-based predictive maintenance system that forecasts failures before they occur
3. Build an autonomous self-healing system using RL-inspired action selection
4. Integrate explainable AI (Gemini/Groq LLMs) for transparent automated decisions
5. Deploy and validate the complete framework on a live cloud environment
6. Evaluate system performance using standard ML metrics and operational KPIs

---

---

## 📌 SLIDE 4 — System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│           Healing Dashboard (Primary UI — Port 5001)             │
│  • Real-time Monitoring  • Auto-Healing  • AI Analysis          │
│  • IP Blocking  • Cloud Simulation  • Service Management       │
└────────────┬─────────────────┬──────────────────┬───────────────┘
             │                 │                  │
             ▼                 ▼                  ▼
  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
  │  ML Model API   │  │  Monitoring     │  │  Network        │
  │  (Port 8080)    │  │  Server         │  │  Analyzer       │
  │                 │  │  (Port 5000)    │  │  (Port 8000)    │
  │ • DDoS Detect   │  │ • Gemini/Groq   │  │ • IP Blocking   │
  │ • Predictive    │  │ • Log Analysis  │  │ • Attack Track  │
  └─────────────────┘  └─────────────────┘  └─────────────────┘
             │                 │                  │
             └─────────────────┼──────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
      ┌─────────────────┐            ┌─────────────────┐
      │  Auto-Healing   │            │  XAI Layer      │
      │  Orchestrator   │            │  Gemini + Groq  │
      │  • System       │            │  3-Section      │
      │  • Container    │            │  Explanations   │
      │  • Resource     │            │                 │
      └─────────────────┘            └─────────────────┘
```

- **5 microservices** running independently on separate ports
- **Auto-healing orchestrator** with modular action system
- **Dual LLM explainability** with automatic fallback

---

---

## 📌 SLIDE 5 — Key Components Implemented

### 1. ML-Based DDoS Detection
- TensorFlow model trained on **CICDDoS2019** benchmark dataset
- Detects: HTTP Flood, SYN Flood, Bot Activity, Port Scans
- Real-time inference via REST API (Port 8080)
- Auto-blocks IPs at threat level ≥ 80%

### 2. Autonomous Auto-Healing System
- RL-inspired healing orchestrator with modular actions:
  - **System actions**: service restart, permissions fix, cache clearing
  - **Container actions**: container restart, start, recreate
  - **Resource actions**: resource cleanup, network restoration
- Post-action verification confirms recovery
- Full healing history audit trail

### 3. Explainable AI (XAI) Layer
- **Google Gemini** (primary) + **Groq LLaMA** (fallback) + **TF-IDF** (last resort)
- Concise 3-section format: What Happened → Quick Fix → Prevention
- Every automated decision accompanied by plain-English explanation

### 4. Predictive Failure Prediction System (see Slide 6 for details)
- XGBoost dual-model approach: classification + time-to-failure regression
- Forecasts system failures **1–24 hours before they occur**
- Early warning system with real-time risk scoring
- Trained on 145 engineered features including 28 predictive indicators

---

---

## 📌 SLIDE 6 — Failure Prediction System (Predictive Maintenance)

### Model Architecture
- **XGBoost** gradient boosting model (with GradientBoosting fallback)
- **Dual-model approach:**
  - **Classification Model** — detects whether an anomaly/failure is imminent (binary: normal vs. failure)
  - **Regression Model** — predicts *time-to-failure* in hours (how soon the failure will happen)

### Feature Engineering
- **145 engineered features** extracted from system metrics, including:
  - **28 predictive indicators** — resource degradation trends, error escalation patterns, service failure signals
  - System metrics: `cpu_percent`, `memory_percent`, `disk_percent`, network I/O
  - Log patterns: `error_count`, `warning_count`, `service_failures`
  - Temporal features: rolling averages, rate of change, trend indicators

### Prediction Capabilities
| Capability | Details |
|-----------|----------|
| **Prediction Horizon** | 1, 6, and 24 hours ahead |
| **Early Detection Rate** | 85% of failures detected >1 hour before occurrence |
| **Mean Lead Time** | ~4.2 hours average advance warning |
| **Time-to-Failure Accuracy** | 78.5% predictions within ±1 hour |
| **Risk Scoring** | Real-time failure risk percentage per service |

### Training & Evaluation Results
| Metric | Result |
|--------|--------|
| Accuracy | 92.3% |
| Precision | 89.0% |
| Recall | 85.0% |
| F1 Score | 86.9% |
| ROC-AUC | 94.6% |
| PR-AUC | 91.2% |
| Time-to-Failure MAE | 2.15 hours |

### How It Works (Flow)
1. **Collect** — System metrics gathered every 30 seconds from 13 critical services
2. **Engineer** — 145 features extracted including degradation trends and error escalation
3. **Predict** — XGBoost classifies normal vs. pre-failure state + estimates time-to-failure
4. **Warn** — Early warnings displayed on dashboard with severity and risk percentage
5. **Act** — Auto-healing orchestrator can proactively take preventive action before failure occurs

### API Endpoints
- `GET /api/predict-failure-risk` — real-time failure risk score
- `GET /api/predict-time-to-failure` — estimated hours until failure
- `GET /api/get-early-warnings` — list of active early warnings

**Evidence:** `model/train_xgboost_model.py`, `model/artifacts/`, `model/PREDICTIVE_MAINTENANCE_README.md`, `scripts/demo-predictive-model.py`, dashboard predictive maintenance page.

---

---

## 📌 SLIDE 7 — Technologies Implemented

| Function | Technologies Used |
|----------|------------------|
| DDoS Detection | TensorFlow, Scikit-learn (ML/Deep Learning) |
| Failure Prediction | XGBoost / GradientBoosting (Predictive Maintenance) |
| Healing Action Decision | RL-inspired orchestrator (Action Selection) |
| Log Analysis & XAI | Google Gemini API, Groq API (LLM-based Explanations) |
| System Monitoring | Flask, Prometheus, WebSocket (Real-time Monitoring) |
| IP Blocking & Tracking | SQLite, Network Analyzer (Persistent Storage) |
| Dashboard UI | HTML/CSS/JS, Flask (Admin Interface) |
| Deployment | Docker, Google Cloud Platform (Containerized Cloud) |
| Notifications | Discord/Slack Webhooks (Real-time Alerts) |

---

---

## 📌 SLIDE 8 — How We Addressed Evaluator Comments

### Comment → Action Summary

| Evaluator Feedback | How We Addressed It |
|---|---|
| Define clear baselines/comparison models | Defined ML metrics (Accuracy, Precision, Recall, F1) using CICDDoS2019 benchmark |
| Clarify real-time performance with ML/RL | Multi-service architecture on separate ports; async monitoring; WebSocket updates |
| Justify synthetic data generation | Combined CICDDoS2019 benchmark + cloud fault simulation engine |
| Discuss security/ethical implications | Human-in-the-loop override; tiered action severity; audit trail |
| Explain technical limitations | Documented 6 limitations with mitigation strategies |
| Justify RL selection | Comparative analysis: RL vs rule-based vs supervised vs expert systems |
| State research gap precisely | Defined 3-fold integration gap: Detection + Healing + Explainability |
| Real-world validation needed | **Live deployment on GCP** at `34.142.246.196:5001` |
| Safety controls for RL module | 5-layer safety architecture (classification → verification → fallback → audit → oversight) |

**20 of 21 comments fully addressed ✅**
**1 partially addressed (formal usability survey pending) 🔄**

---

---

## 📌 SLIDE 9 — Real-World Deployment & Validation

### Live Cloud Deployment ✅
- Deployed on **Google Cloud Platform (GCP)**
- Accessible at: `http://34.142.246.196:5001/`
- Running continuously with real-time monitoring

### What's Running Live:
- ✅ DDoS detection with ML model predictions
- ✅ Automatic IP blocking (auto + manual)
- ✅ Auto-healing with fault detection & recovery
- ✅ AI-powered log analysis (Gemini/Groq)
- ✅ Cloud simulation & fault injection testing
- ✅ Predictive maintenance forecasting
- ✅ 13 critical services monitored every 30 seconds
- ✅ Docker containerized deployment

### Testing Conducted:
- DDoS attack simulation against live instance
- Service crash injection and auto-recovery
- AI explanation quality verification
- Predictive maintenance failure forecasting validation

---

---

## 📌 SLIDE 10 — Evaluation Metrics & Results

### DDoS Detection Performance

| Metric | Target | Status |
|--------|--------|--------|
| Accuracy | > 95% | ✅ Tracked on dashboard |
| Precision | > 90% | ✅ Tracked on dashboard |
| Recall | > 95% | ✅ Tracked on dashboard |
| F1-Score | > 92% | ✅ Tracked on dashboard |
| False Positive Rate | < 5% | ✅ Monitored continuously |

### Operational Performance

| Metric | Target | Status |
|--------|--------|--------|
| Mean Time to Detect | < 30 seconds | ✅ Achieved (30s monitoring cycle) |
| Mean Time to Heal | < 30 seconds | ✅ Achieved (auto-healing) |
| Healing Success Rate | > 90% | ✅ Tracked in healing history |
| Failure Prediction Lead Time | 1-24 hours advance | ✅ XGBoost (mean 4.2hr lead time) |
| Early Detection Rate | > 85% | ✅ 85% failures detected >1hr ahead |
| Prediction Accuracy (Time) | Within ±1 hour | ✅ 78.5% accuracy |

---

---

## 📌 SLIDE 11 — Challenges Faced & Solutions

| Challenge | Solution |
|-----------|----------|
| **False positive DDoS detection** | ML confidence threshold (≥80%) + multi-pattern attack classification before auto-blocking |
| **AI provider outages** | Dual-provider fallback: Gemini → Groq → TF-IDF (local). Automatic switching ensures continuous AI analysis |
| **Service cascading failures** | Independent microservice architecture — each service on its own port with health checks |
| **Model drift with evolving attacks** | XGBoost predictive maintenance + model retraining capability + real-time metrics monitoring |
| **Making AI explanations understandable** | Concise 3-section LLM format (What Happened → Quick Fix → Prevention). Verified with `verify_conciseness.py` |
| **Safe autonomous operation** | 5-layer safety architecture: action classification, verification, fallback, audit, human oversight |

---

---

## 📌 SLIDE 12 — Implementation Progress

| Phase | Status |
|-------|--------|
| Research & Design | ✅ Complete |
| Data Preparation (CICDDoS2019) | ✅ Complete |
| ML Model Development (TensorFlow + XGBoost) | ✅ Complete |
| Core System (Monitoring, Healing, IP Blocking) | ✅ Complete |
| XAI & Dashboard (Gemini/Groq + Web UI) | ✅ Complete |
| Cloud Deployment (GCP + Docker) | ✅ Complete |
| Evaluation & Documentation | 🔄 In Progress |

### Remaining Work:
- Formal usability survey (Likert-scale questionnaire)
- Expanded scalability testing (100+ nodes)
- LIME/SHAP integration alongside LLM explanations
- Final benchmarking report

---

---

## 📌 SLIDE 13 — Demo / Evidence

### Live System Evidence:

| Feature | Proof |
|---------|-------|
| DDoS detection | ML Model API active at Port 8080; real-time predictions |
| IP blocking | Auto + manual blocking; SQLite persistence; unblock capability |
| Auto-healing | Service crash → automatic recovery → verification → audit log |
| AI explanations | Gemini/Groq-powered 3-section analysis visible on dashboard |
| Cloud simulation | Fault injection (CPU spike, memory leak, service crash) |
| Predictive maintenance | XGBoost early warning 1-24 hours before failures |
| Live deployment | GCP VM at `http://34.142.246.196:5001/` |

### Demo Flow:
1. Show Healing Dashboard with real-time monitoring
2. Demonstrate DDoS detection → auto IP blocking
3. Show **predictive maintenance** page — failure risk scores & early warnings
4. Inject a fault via Cloud Simulation → show auto-healing
5. Show AI explanation for a healing action
6. Show healing history audit trail

---

---

## 📌 SLIDE 14 — Future Work

### Short-Term (Next 2 Months):
- Conduct formal **administrator usability survey** (Likert-scale)
- Integrate **LIME/SHAP** for model-level explainability alongside LLM explanations
- Expand scalability testing to **100+ nodes** using Docker Compose

### Medium-Term:
- Implement **federated learning** for distributed fault management across multiple clusters
- Add **Kubernetes-native** integration for container orchestration environments
- Develop a **mobile companion app** for on-the-go monitoring

### Long-Term Vision:
- Open-source the framework for community adoption
- Partner with cloud providers for **plugin marketplace** distribution
- Extend to **edge computing** and **IoT** environments

---

---

## 📌 SLIDE 15 — Thank You

### Autonomous AI Bot for Self-Healing and Proactive Server Health Management in Distributed Systems

**Group 29 | BICT Honors Degree 2025**

**University of Sri Jayewardenepura**
**Faculty of Technology**

---

**Live Demo:** `http://34.142.246.196:5001/`

**Questions?**

---
