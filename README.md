# Security-agent-in-VANETs-AI-Based-Intrusion-Detection

This internship project implements AI-driven Red (attack) and Blue (defense) agents for securing Vehicular Ad-hoc Networks (VANETs) using SUMO and Secure Multiparty Computation (MPC).


## Project Overview

This project simulates cyber attacks and defenses in VANETs through:
- **Red Agent**: Launches multi-layer attacks (Sybil, DDoS, GPS spoofing) across OSI layers.
- **Blue Agent**: AI-based intrusion detection system using ML/DL models.
- **Privacy Layer**: MPC protocols for secure vehicle-to-infrastructure and vehicle-to-vehicle communication.

## Key Features

- **Multi-Layer Attack Simulation**
  - Network, physical, and application layer attacks.
  - Realistic threat modeling in vehicular networks.
  
- **AI-Powered Enhancement**
  - Optimizes traffic flow using AI techniques.

- **Full-Stack Simulation**
  - SUMO for traffic dynamics.

- **Model Context Protocol**
  - Enables agents to have control over the tools.

## Tools & Technologies

| Category              | Technologies                                                                 |
|-----------------------|------------------------------------------------------------------------------|
| **Simulation**        |  SUMO 1.22                                         |
| **AI/ML**            | fast-agent,fast-mcp                                   |
| **Languages**         | HTML, Python 3.10+                                         |
| **Optional Tools**    | Ollama                                     |

## Installation

### Prerequisites
- Python 3.10+
- SUMO 1.22

### Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/KyleDottin/Security-agent-in-VANETs-AI-Based-Intrusion-Detection.git
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the MCP Server**
   ```bash
   python MCP/MCP_server.py
   ```

## Contributors
- **Kyle Dottin**
- **Nassim Anemiche**


