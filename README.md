<div align="center">
  <img src="assets/logo_milimo.png" alt="Milimo Quantum Logo" width="200"/>
  
  # Milimo Quantum ⚛️

  ### The Ultimate Quantum-AI Research OS
  
  **Author:** [Mainza Kangombe](https://www.linkedin.com/in/mainza-kangombe-6214295/)
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Qiskit](https://img.shields.io/badge/Qiskit-v1.4-6f42c1)](https://qiskit.org/)
  [![React](https://img.shields.io/badge/React-18-61dafb)](https://reactjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)

  *Harness the power of quantum computing through an autonomous, hybrid AI-orchestrated research platform.*
</div>


> [!IMPORTANT]
> Milimo is currently in **active development**. The full version will be released on **March 31st, 2026**.

---


## 🌌 Vision

**Milimo Quantum** has evolved from a toolset into a **Hybrid Research OS**. By uniting **Qiskit SDK v1.4** with a sophisticated multi-agent network, it enables autonomous scientific discovery. It bridges the gap between natural language intent and complex quantum execution across IBM, D-Wave, and Amazon Braket, powered by local-first inference and hardened security.

## ✨ Key Features

- 🧠 **Autonomous Multi-Agent Orchestration**: A network of 14+ specialized agents (Orchestrator, Research, Chemistry, Finance, etc.) handling the full lifecycle from hypothesis to quantum code.
- 🧬 **MQDD (Milimo Quantum Drug Discovery)**: Specialized extension for molecular simulation and property prediction using Variational Quantum Eigensolvers (VQE).
- 🔬 **Autoresearch-MLX**: Native integration for local research loops, fine-tuning, and ultra-fast inference on Apple Silicon via unified memory.
- ⚡ **Quantum Execution Engine**: Native support for Qiskit v1.4, Aer simulation, GPU acceleration, and direct QPU execution.
- 🕸️ **Graph IQ & Temporal Memory**: Deep knowledge retrieval using **Neo4j** and deterministic relational paths, combined with **FalkorDB** for agent memory.
- 🛡️ **Hardened Isolation**: Secure execution sandbox utilizing AST parsing and import whitelisting, with a roadmap toward gVisor/OS-level isolation.
- 📱 **Omni-channel Dashboard**: Premium React 18 web interface with live circuit visualizers and a React Native mobile monitor for global job tracking.

---

## 🧱 Architecture & Project Structure

The platform is built on a modular, scalable architecture designed for local-heavy, hybrid-cloud performance.

| System Layer | Description | Path |
| --- | --- | --- |
| **Presentation (Frontend)** | React 18 dashboard with extension panels (MQDD, Autoresearch). | `/frontend` |
| **Research Engine (MLX)** | Local-first MLX training and inference for Apple Silicon. | `/autoresearch-mlx` |
| **Orchestration (Backend)** | FastAPI core, Celery/Redis for async job routing and project isolation. | `/backend` |
| **Enterprise Monitor (Mobile)**| React Native client for real-time experiment monitoring. | `/mobile` |
| **Infrastructure** | Keycloak Auth, Neo4j, PostgreSQL, and Redis service containers. | `/` |

---

## 🛠️ Technology Stack

* **AI/ML**: MLX (Apple Silicon), Ollama, OpenAI, Anthropic, Google GenAI
* **Quantum**: Qiskit (< 2.0.0), D-Wave Ocean, Amazon Braket
* **Frontend/Mobile**: React 18, Vite, Tailwind CSS, Monaco Editor, React Native (Expo)
* **Backend**: Python 3.12, FastAPI, Celery, Redis
* **Data**: PostgreSQL, Neo4j (Graph), FalkorDB (Memory), ChromaDB (Vector)
* **Auth/Security**: Keycloak (OAuth2), AST Sandbox
* **DevOps**: Docker, Docker Compose, Alembic

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18+)
- **Python** (3.12)
- **Docker & Docker Compose**
- **Ollama** (Optional, for local agent inference)
- **Apple Silicon Mac** (Required for MLX-native features)

### Quick Start

#### 1. Boot Infrastructure & Frontend (Docker)
```bash
./start-docker-mlx.sh
```
*This starts the database, cache, graph stores, and the React frontend.*

#### 2. Start the MLX Native Backend (Mac Host)
To leverage Unified Memory on Mac, run the backend natively:
```bash
./start-backend-mlx.sh
```

#### 3. Initialize Authentication (Required)
Configure Keycloak for first-time use:
```bash
./setup-keycloak.sh
```
*Login with `admin` / `admin` at `http://localhost:5173`.*

#### 4. To Shut Down:
```bash
./stop-backend-mlx.sh && ./stop-docker.sh
```

---

## 📜 License

Governed under the **MIT License**.

<div align="center">
  <i>Bringing the quantum future to the minds of today.</i>
</div>
