# Security-agent-in-VANETs-AI-Based-Intrusion-Detection

Internship implementing AI-driven Red (attack) and Blue (defense) agents for securing Vehicular Ad-hoc Networks (VANETs) using the Veins simulator and Secure Multiparty Computation (MPC).

## Project Overview

This project simulates cyber attacks and defenses in VANETs through:
- **Red Agent**: Launches multi-layer attacks (Sybil, DDoS, GPS spoofing) across OSI layers
- **Blue Agent**: AI-based intrusion detection system using ML/DL models
- **Privacy Layer**: MPC protocols for secure vehicle-to-infrastructure communication
- **Veins Framework**: Realistic network stack simulation with OMNeT++ and SUMO

## Key Features

- **Multi-Layer Attack Simulation**
  - Network, transport, and application layer attacks
  - Realistic threat modeling in vehicular networks
  
- **AI-Powered Defense**
  - Anomaly detection and classification models
  - Real-time response mechanisms

- **Privacy-Preserving MPC**
  - Secure data sharing between vehicles
  - MP-SPDZ/PySyft integration

- **Full-stack Simulation**
  - SUMO for traffic dynamics
  - OMNeT++ for network protocol simulation

## Tools & Technologies

| Category              | Technologies                                                                 |
|-----------------------|------------------------------------------------------------------------------|
| **Simulation**        | Veins 5.2, OMNeT++ 6.0, SUMO 1.18                                           |
| **AI/ML**            | TensorFlow/PyTorch, Scikit-learn, XGBoost                                   |
| **MPC**              | MP-SPDZ, PySyft                                                             |
| **Languages**         | C++ (OMNeT++ modules), Python 3.10+                                         |
| **Optional Tools**    | Ollama/LM Studio (for LLM integration)                                      |

## Installation

### Prerequisites
- Ubuntu 22.04 LTS (recommended)
- Python 3.10+
- SUMO 1.18
- OMNeT++ 6.0

### Setup
1. **Install Veins Framework**
   ```bash
   git clone https://github.com/KyleDottin/Security-agent-in-VANETs-AI-Based-Intrusion-Detection.git
