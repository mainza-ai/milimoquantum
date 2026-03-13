# Milimo Quantum Drug Discovery (MQDD)

Milimo Quantum Drug Discovery (MQDD) is an AI-native system that functions as an expert AI Co-Scientist, designed to accelerate the discovery of new medicines. This platform fuses the advanced reasoning of Gemini 2.5 Pro with a multi-agent framework, multimodal APIs, and quantum simulation capabilities to streamline and enhance the entire drug discovery pipeline.

## Run Locally
**Prerequisites:**  Node.js

1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Core Technologies

- **AI Model:** Google Gemini 2.5 Pro
- **Real-time Conversation:** Google Gemini Live API for voice discussions
- **Frontend:** React with TypeScript
- **Visualization:** 3Dmol.js and SmilesDrawer for molecular rendering
- **Architecture:** Multi-agent framework for specialized tasks

## Key Features

- **Automated Research Workflow:** A sophisticated multi-agent system handles tasks from target identification and literature review to molecular design and property prediction.
- **Quantum Simulation:** Integrates mock quantum simulations to calculate molecular binding energies, providing a crucial metric for candidate viability.
- **Interactive Voice Discussion:** Allows researchers to have a natural, real-time voice conversation with the AI to discuss results, ask follow-up questions, and brainstorm next steps.
- **Context-Aware Refinement:** The AI can refine existing results based on user feedback, generating improved candidates and updated experimental plans.
- **Comprehensive Data Exploration:** An interactive results explorer provides detailed views of candidate molecules, ADMET properties, synthesis plans, and an evolving knowledge graph.
- **Data Export:** Easily export results to common formats like Markdown reports (.md), candidate data (.csv), and 3D molecule files (.sdf).

## Created By

**Mainza Kangombe**
- **LinkedIn:** [linkedin.com/in/mainza-kangombe-6214295](https://www.linkedin.com/in/mainza-kangombe-6214295/)
