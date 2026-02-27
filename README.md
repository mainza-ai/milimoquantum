<div align="center">
  <img src="assets/logo_milimo.png" alt="Milimo Quantum Logo" width="200"/>
  
  # Milimo Quantum ⚛️

  ### The Ultimate Quantum-AI Application Platform
  
  **Author:** [Mainza Kangombe](https://www.linkedin.com/in/mainza-kangombe-6214295/)
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Qiskit](https://img.shields.io/badge/Qiskit-v1.4-6f42c1)](https://qiskit.org/)
  [![React](https://img.shields.io/badge/React-18-61dafb)](https://reactjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)

  *Harness the power of quantum computing across every major vertical through natural language AI orchestration.*
</div>

---

## 🌌 Vision

**Milimo Quantum** is a next-generation, AI-powered quantum computing platform that unites the **Qiskit SDK v1.4** ecosystem with multi-agent Large Language Models. It democratizes quantum computing, allowing users spanning chemistry, finance, cryptography, and more to effortlessly formulate, execute, and analyze quantum algorithms through natural language chat interfaces.

By treating quantum programming as accessible conversations, Milimo Quantum empowers researchers to cut down discovery times and seamlessly bridge classical workflows with advanced quantum execution on IBM, D-Wave, and Amazon Braket hardware.

## ✨ Key Features

- 🧠 **Multi-Agent Orchestration Engine**: Built with a robust LLM agent network consisting of 14 specialized domain agents (Orchestrator, Planning, Research, Chemistry, Finance, Crypto, QML, Optimization, Code, etc.) processing natural language to quantum code.
- ⚡ **Quantum Execution Engine**: Native reliance on the newest Qiskit SDK v1.4 with support for Aer simulation, GPU acceleration, and actual QPU target execution through IBM Runtime and Amazon Braket.
- 🧬 **Domain-Specific Power**: Easily run molecular simulation (VQE), portfolio optimization, integer factorization (Shor), and combinatorial optimization (QAOA/D-Wave) tailored explicitly to distinct verticals.
- 🤖 **Hybrid AI Agnosticism**: Deep integration capable of shifting inference from local private clusters leveraging **Ollama** (Llama 3.x, Mistral, DeepSeek) to frontier cloud APIs (OpenAI, Anthropic, Gemini).
- 🕸️ **Graph Intelligence & Temporal Memory**: Intelligent storage utilizing **Neo4j** for domain knowledge graphs, **FalkorDB + Graphiti** for agent temporal memory, and ChromaDB for embedding search.
- 📱 **Omni-channel Interfaces**: Premium **React 18** web dashboard with sandboxed circuit visualizers, combined with a **React Native** Mobile Application for enterprise job and experiment progression monitoring.

---

## 🧱 Architecture & Project Structure

The platform comprises an expansive, layered technology stack:

| System Layer | Description | Path |
| --- | --- | --- |
| **Presentation (Frontend)** | React 18, Vite, TailwindCSS dashboard featuring Artifact panels, code execution widgets (Monaco), and circuit views. | `/frontend` |
| **Enterprise Monitor (Mobile)**| React Native iOS/Android app to monitor live quantum job statuses globally. | `/mobile` |
| **Orchestration (Backend)** | FastAPI, Python-based agent core utilizing Celery/Redis for job queues and asynchronous routing. | `/backend` |
| **Documentation** | Deep-dive research reports, gap analysis, and phased development roadmaps. | `/development_docs` & `/docs` |

---

## 🛠️ Technology Stack

* **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Monaco Editor
* **Mobile**: React Native, Expo
* **Backend Framework**: Python 3.12, FastAPI, Uvicorn, Celery, Redis
* **Quantum Tooling**: Qiskit (< 2.0.0), Qiskit Aer, D-Wave Ocean, Amazon Braket
* **AI & LLM Integration**: Ollama, OpenAI, Anthropic, Google GenAI
* **Database & Knowledge Store**: PostgreSQL, Alembic, Neo4j, FalkorDB, ChromaDB, DuckDB
* **Auth**: Keycloak (OAuth2, RBAC)
* **DevOps**: Docker, Docker Compose

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed locally:
- **Node.js** (v18+)
- **Python** (3.11/3.12)
- **Docker & Docker Compose**
- **Ollama** (for local agent inference)
- Supported Quantum API keys (IBM Quantum / AWS Braket / D-Wave Leap) *(Optional but recommended)*

### Quick Start

Milimo Quantum utilizes Docker to streamline localized deployment.

#### Standard Deployment (Docker-only)
1. **Boot Core Services & Architecture:**
   Start PostgreSQL, Redis, Neo4j, FalkorDB, and the Python backend/React frontend using docker-compose.
   ```bash
   ./start-docker.sh
   # Or directly: docker compose --profile dev up -d
   ```
   *The React quantum dashboard will begin running on `http://localhost:5173` and the backend on `http://localhost:8000`.*

#### Apple Silicon Native Inference (Hybrid Deploy)
If you wish to use the ultra-fast Apple Silicon MLX models via Unified Memory on a Mac host, the backend must run outside of the Linux Docker container.
1. **Boot Infrastructure & Frontend (Docker):**
   ```bash
   ./start-docker-mlx.sh
   ```
2. **Start the MLX Native Backend (Mac Host):**
   ```bash
   ./start-backend-mlx.sh
   ```

#### Initialize Authentication (Required)
Regardless of your deployment method, once the Docker infrastructure is running, you must configure the Keycloak realm, client, and admin user to log in:
```bash
./setup-keycloak.sh
```
*You can now log in to the web dashboard using username: `admin` and password: `admin`.*

#### To Shut Down:
```bash
./stop-backend-mlx.sh # Kills the native Python backend (if using hybrid)
./stop-docker.sh      # Tears down the docker infrastructure
```

#### Mobile Support

3. **Mobile Client (Optional):**
   ```bash
   cd mobile
   npm install
   npx expo start
   ```

---

## 📜 License

This application and its associated software architecture is governed under the **MIT License**.

<div align="center">
  <i>Developed to bring the quantum future to the minds of today.</i>
</div>
