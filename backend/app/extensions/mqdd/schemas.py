from typing import List, Optional
from pydantic import BaseModel, Field

class AdmetProperty(BaseModel):
    value: str = Field(description="The predicted value (e.g., '-2.5', 'High', 'Low').")
    evidence: str = Field(description="A brief justification for the value.")
    score: float = Field(description="A numerical score from 0.0 (very good) to 1.0 (very bad).")

class AdmetSchema(BaseModel):
    logP: AdmetProperty
    logS: AdmetProperty
    permeability: AdmetProperty
    herg: AdmetProperty
    toxicity: AdmetProperty

class AdmetPredictionResponse(BaseModel):
    admet: AdmetSchema
    painsAlerts: List[str] = Field(description="List of matched PAINS filter names, or empty.")

class Interaction(BaseModel):
    type: str = Field(description="Type: 'HydrogenBond', 'Hydrophobic', or 'PiStacking'.")
    residue: str = Field(description="The interacting amino acid residue (e.g., 'ALA-225').")
    ligandAtoms: List[int] = Field(description="Indices of atoms in the ligand involved.")
    proteinAtoms: List[int] = Field(description="Indices of atoms in the protein involved.")
    distance: Optional[float] = Field(default=None, description="Distance in angstroms.")

class MoleculeCandidate(BaseModel):
    name: str
    smiles: str
    bindingEnergy: Optional[float] = None
    saScore: Optional[float] = None
    admet: Optional[AdmetSchema] = None
    painsAlerts: Optional[List[str]] = None
    interactions: Optional[List[Interaction]] = None

class TargetIdentificationResponse(BaseModel):
    pdbId: Optional[str] = Field(description="A relevant 4-character PDB ID, or null.")

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = Field(description="'candidate', 'target', or 'concept'.")

class GraphEdge(BaseModel):
    source: str = Field(alias="from")
    target: str = Field(alias="to")
    label: str

class KnowledgeGraphUpdate(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

    class Config:
        populate_by_name = True

class LiteratureReference(BaseModel):
    title: str
    url: str
    summary: str

class ExperimentalPlannerResponse(BaseModel):
    summary: str
    experimentalPlan: List[str]
    knowledgeGraphUpdate: KnowledgeGraphUpdate

class MqddResultData(BaseModel):
    summary: str = ""
    pdbId: Optional[str] = None
    molecules: List[MoleculeCandidate] = []
    literature: List[LiteratureReference] = []
    experimentalPlan: List[str] = []
    retrosynthesisPlan: List[str] = []
    knowledgeGraphUpdate: Optional[KnowledgeGraphUpdate] = None
    proactiveSuggestions: List[str] = []
    failureAnalysisReport: Optional[str] = None
