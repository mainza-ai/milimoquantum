
export enum AgentName {
  TARGET_IDENTIFICATION = 'Target ID Agent',
  LITERATURE = 'Literature Agent',
  MOLECULAR_DESIGN = 'Molecular Design Agent',
  PROPERTY_PREDICTION = 'ADMET Agent',
  EXPERIMENTAL_PLANNER = 'Experimental Planner Agent',
  QUANTUM_SIMULATION = 'Quantum Simulation Agent',
  RETROSYNTHESIS = 'Retrosynthesis Agent',
  KNOWLEDGE_GRAPH = 'Knowledge Graph Agent',
  FAILURE_ANALYSIS = 'Failure Analysis Agent',
  HYPOTHESIS = 'Hypothesis Agent',
  INTERACTION_ANALYSIS = 'Interaction Analysis Agent',
  SYNTHESIZABILITY = 'Synthesizability Agent',
}

export enum AgentStatus {
  IDLE = 'idle',
  WORKING = 'working',
  DONE = 'done',
  ERROR = 'error',
}

export interface Agent {
  name: AgentName;
  status: AgentStatus;
  description: string;
  message?: string;
}

export interface AdmetProperty {
    value: string;
    evidence?: string; // Justification or, for toxicity, a SMARTS pattern of the toxicophore.
    score?: number; // A numerical score from 0.0 (good) to 1.0 (bad).
}

export interface AdmetProperties {
  logP: AdmetProperty; // Lipophilicity
  logS: AdmetProperty; // Aqueous Solubility
  permeability: AdmetProperty; // e.g., Caco-2
  herg: AdmetProperty; // Cardiotoxicity
  toxicity: AdmetProperty;
}

export interface Interaction {
    type: 'HydrogenBond' | 'Hydrophobic' | 'PiStacking';
    residue: string;
    ligandAtoms: number[];
    proteinAtoms: number[];
    distance?: number;
}

export interface Molecule {
  name: string;
  smiles: string;
  admet?: AdmetProperties;
  bindingEnergy?: number;
  interactions?: Interaction[];
  painsAlerts?: string[];
  saScore?: number;
}

export interface LiteratureReference {
    title: string;
    url: string;
    summary: string;
}

export interface GraphNode {
    id: string;
    label: string;
    type: 'candidate' | 'target' | 'concept';
}

export interface GraphEdge {
    from: string;
    to: string;
    label: string;
}

export interface KnowledgeGraph {
    nodes: GraphNode[];
    // Fix: Removed an obsolete comment.
    edges: GraphEdge[];
}

export interface ResultData {
    pdbId?: string;
    summary: string;
    molecules: Molecule[];
    literature: LiteratureReference[];
    experimentalPlan: string[];
    retrosynthesisPlan: string[];
    knowledgeGraphUpdate: KnowledgeGraph;
    proactiveSuggestions: string[];
    failureAnalysisReport?: string;
}

export interface Message {
  id: string;
  sender: 'user' | 'ai' | 'system';
  text: string;
  data?: ResultData;
  attachment?: {
    name: string;
  };
}
