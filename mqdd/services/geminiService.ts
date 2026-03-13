
import { GoogleGenAI, Type, LiveServerMessage, Modality, Blob } from "@google/genai";
import { AgentName, ResultData, Molecule, KnowledgeGraph, Message, AgentStatus } from '../types';

if (!process.env.API_KEY) {
    throw new Error("API_KEY environment variable not set");
}

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const model = 'gemini-2.5-pro';

export enum Intent {
  DRUG_DISCOVERY_WORKFLOW = 'DRUG_DISCOVERY_WORKFLOW',
  REFINEMENT_WORKFLOW = 'REFINEMENT_WORKFLOW',
  GENERAL_CHAT = 'GENERAL_CHAT',
}

const intentSchema = {
    type: Type.OBJECT,
    properties: {
        intent: { type: Type.STRING },
    },
    required: ['intent'],
};

export const determineIntent = async (
    prompt: string,
    hasExistingResults: boolean,
): Promise<{ intent: Intent }> => {
    try {
        const context = `Context: An existing set of drug discovery results ${hasExistingResults ? 'DOES' : 'DOES NOT'} exist.`;
        const routingPrompt = `You are a router agent for a sophisticated drug discovery AI assistant. Your task is to classify the user's intent based on their prompt.

The user's prompt is: "${prompt}"

${context}

Classify the intent into one of a three categories:
1. DRUG_DISCOVERY_WORKFLOW: The user wants to start a NEW drug discovery project from scratch. This usually involves a specific biological target, a disease, or a request to design molecules. Examples: "Find an inhibitor for BRAF V600E", "Design a non-toxic molecule for Alzheimer's targeting amyloid beta". This is the default for ambiguous research-oriented prompts.
2. REFINEMENT_WORKFLOW: The user wants to MODIFY or ask a follow-up question about the EXISTING results. This is only possible if existing results are present. Examples: "Replace the nitro group on the lead candidate", "Can you make it more soluble?", "Find a better synthesis path for molecule X".
3. GENERAL_CHAT: The user is asking a general knowledge question, making a simple calculation, greeting the AI, or asking a meta-question about the results that doesn't require re-running the workflow. Examples: "Hello", "What is 1 + 2?", "What is a kinase?", "Summarize the results in one sentence."

If existing results DO NOT exist, the intent can NEVER be 'REFINEMENT_WORKFLOW'. Your choice must be either 'DRUG_DISCOVERY_WORKFLOW' or 'GENERAL_CHAT'.

Respond with only a JSON object with a single key "intent" and one of the three string values: "DRUG_DISCOVERY_WORKFLOW", "REFINEMENT_WORKFLOW", or "GENERAL_CHAT".`;
        
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-pro',
            contents: routingPrompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: intentSchema,
                temperature: 0,
            }
        });
        
        const result = JSON.parse(response.text);
        
        if (result.intent === Intent.REFINEMENT_WORKFLOW && !hasExistingResults) {
            console.warn("Router suggested REFINEMENT_WORKFLOW without existing results. Overriding to DRUG_DISCOVERY_WORKFLOW.");
            return { intent: Intent.DRUG_DISCOVERY_WORKFLOW };
        }

        return result;

    } catch (error) {
        console.error("Error in determineIntent:", error);
        // Fallback to a safe default if router fails
        return { intent: hasExistingResults ? Intent.REFINEMENT_WORKFLOW : Intent.DRUG_DISCOVERY_WORKFLOW };
    }
};

const chatResponseSchema = {
    type: Type.OBJECT,
    properties: {
        text: { type: Type.STRING, description: "The conversational, helpful response to the user's prompt." },
        suggestions: {
            type: Type.ARRAY,
            description: "An array of 2-3 concise, actionable suggestions for the user's next step, based on the conversation.",
            items: { type: Type.STRING }
        }
    },
    required: ['text', 'suggestions']
};

export const runChat = async (
    prompt: string,
    history: Message[]
): Promise<{ text: string; suggestions: string[] }> => {
     try {
        const chatHistory = history
          .filter(m => m.sender === 'user' || m.sender === 'ai')
          .slice(-10) // Take last 10 messages for context
          .map(m => ({
            role: m.sender === 'user' ? 'user' : 'model',
            parts: [{ text: m.text }]
          }));

        const fullConversation = [
            ...chatHistory,
            { role: 'user' as const, parts: [{ text: prompt }] }
        ];

        const systemInstruction = `You are Milimo, an AI Co-Scientist for drug discovery. Be helpful and conversational. ALWAYS provide a primary 'text' response. Additionally, provide 2-3 concise, actionable 'suggestions' for the user's next step in the conversation or workflow. Respond ONLY with a valid JSON object matching the specified schema.`;
        
        const response = await ai.models.generateContent({
            model,
            contents: fullConversation,
            config: {
                systemInstruction,
                responseMimeType: "application/json",
                responseSchema: chatResponseSchema,
            },
        });
        
        return JSON.parse(response.text);
    } catch(error) {
        console.error("Error in runChat:", error);
        return { text: "I'm sorry, I encountered an error trying to respond. Please try again.", suggestions: [] };
    }
}


const moleculeSchema = {
    type: Type.OBJECT,
    properties: {
        name: { type: Type.STRING },
        smiles: { type: Type.STRING },
    },
    required: ['name', 'smiles'],
};

const admetPropertySchema = {
    type: Type.OBJECT,
    properties: {
        value: { type: Type.STRING, description: "The predicted value (e.g., '-2.5', 'High', 'Low')." },
        evidence: { type: Type.STRING, description: "A brief justification for the value. For toxicity, if the value is 'Medium' or 'High', this MUST be a SMARTS pattern representing the responsible toxicophore. Otherwise, it should be a textual reason." },
        score: { type: Type.NUMBER, description: "A numerical score from 0.0 (very good) to 1.0 (very bad) representing the property. For toxicity, higher is worse." }
    },
    required: ['value', 'score']
};

const admetSchema = {
    type: Type.OBJECT,
    properties: {
        logP: admetPropertySchema,
        logS: admetPropertySchema,
        permeability: admetPropertySchema,
        herg: admetPropertySchema,
        toxicity: admetPropertySchema,
    },
    required: ['logP', 'logS', 'permeability', 'herg', 'toxicity'],
};

const propertyPredictionSchema = {
    type: Type.OBJECT,
    properties: {
        admet: admetSchema,
        painsAlerts: {
            type: Type.ARRAY,
            description: "An array of names for any matched PAINS filters (e.g., 'anil_di_alk_A'). Should be an empty array if no PAINS are detected.",
            items: { type: Type.STRING }
        }
    },
    required: ['admet', 'painsAlerts']
};

const pdbIdSchema = {
    type: Type.OBJECT,
    properties: {
        pdbId: { 
            type: Type.STRING, 
            description: "A relevant 4-character Protein Data Bank (PDB) ID for the protein target. Should be null if a specific, valid ID cannot be determined."
        },
    },
    required: ['pdbId'],
};

const interactionSchema = {
    type: Type.ARRAY,
    items: {
        type: Type.OBJECT,
        properties: {
            type: { type: Type.STRING, description: "Type of interaction: 'HydrogenBond', 'Hydrophobic', or 'PiStacking'." },
            residue: { type: Type.STRING, description: "The interacting amino acid residue (e.g., 'ALA-225')." },
            ligandAtoms: { type: Type.ARRAY, items: { type: Type.INTEGER }, description: "Indices of atoms in the ligand involved." },
            proteinAtoms: { type: Type.ARRAY, items: { type: Type.INTEGER }, description: "Indices of atoms in the protein involved." },
            distance: { type: Type.NUMBER, description: "Distance in angstroms, primarily for Hydrogen Bonds." },
        },
        required: ['type', 'residue', 'ligandAtoms', 'proteinAtoms'],
    }
};

const knowledgeGraphSchema = {
    type: Type.OBJECT,
    properties: {
        nodes: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    id: { type: Type.STRING, description: "A unique identifier for the node (e.g., the molecule name or concept)." },
                    label: { type: Type.STRING, description: "The display name for the node." },
                    type: { type: Type.STRING, description: "The type of node: 'candidate', 'target', or 'concept'." }
                },
                required: ['id', 'label', 'type']
            }
        },
        edges: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    from: { type: Type.STRING, description: "The ID of the source node." },
                    to: { type: Type.STRING, description: "The ID of the target node." },
                    label: { type: Type.STRING, description: "A label describing the relationship (e.g., 'inhibits', 'related to')." }
                },
                required: ['from', 'to', 'label']
            }
        }
    },
    required: ['nodes', 'edges']
};


const runAgent = async (
    agentName: AgentName,
    prompt: string,
    updateStatus: (agent: AgentName, status: AgentStatus, message: string) => void
): Promise<any> => {
    updateStatus(agentName, AgentStatus.WORKING, `Executing ${agentName}...`);
    try {
        let response;
        switch (agentName) {
            case AgentName.TARGET_IDENTIFICATION:
                response = await ai.models.generateContent({
                    model,
                    contents: `Target ID Agent: Parse the user's research goal: "${prompt}". Identify the specific protein target. Find a relevant 4-character PDB ID for this target's structure. If no specific PDB ID can be confidently identified, return null.`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: pdbIdSchema,
                        thinkingConfig: { thinkingBudget: 2048 }
                    }
                });
                return JSON.parse(response.text);

            case AgentName.LITERATURE:
                response = await ai.models.generateContent({
                    model,
                    contents: `Literature Agent: Review recent scientific literature and patent databases related to: "${prompt}". Identify key targets, existing compounds, and gaps in research. Use Google Search grounding to ensure information is up-to-date.`,
                    config: { tools: [{ googleSearch: {} }], thinkingConfig: { thinkingBudget: 8192 } },
                });
                return { text: response.text, groundingChunks: response.candidates?.[0]?.groundingMetadata?.groundingChunks };

            case AgentName.MOLECULAR_DESIGN:
                 response = await ai.models.generateContent({
                    model,
                    contents: `Molecular Design Agent: ${prompt}`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: {
                            type: Type.ARRAY,
                            items: moleculeSchema
                        },
                        thinkingConfig: { thinkingBudget: 8192 }
                    }
                });
                return JSON.parse(response.text);

            case AgentName.PROPERTY_PREDICTION:
                 response = await ai.models.generateContent({
                    model,
                    contents: `ADMET Agent: For the molecule with SMILES string "${prompt}", provide a detailed analysis. Predict: 1. logP (lipophilicity) 2. logS (aqueous solubility) 3. Caco-2 permeability (as 'High' or 'Low') 4. hERG inhibition risk (as 'High', 'Medium', or 'Low') 5. General toxicity risk. 6. Screen for PAINS substructures from standard filters. Respond in JSON format with keys: 'admet' (an AdmetProperties object) and 'painsAlerts' (an array of matched PAINS filter names, or an empty array if none). Each property key inside 'admet' should map to an AdmetProperty object.`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: propertyPredictionSchema,
                        thinkingConfig: { thinkingBudget: 8192 }
                    }
                });
                return JSON.parse(response.text);
            
            case AgentName.QUANTUM_SIMULATION:
                response = await ai.models.generateContent({
                    model,
                    contents: `Quantum Simulation Agent: For the molecule with SMILES string "${prompt}", perform a mock quantum simulation to calculate its binding energy to its primary target. Provide the result as a single numerical value in kJ/mol.`,
                     config: { thinkingConfig: { thinkingBudget: 8192 } }
                });
                const bindingEnergyText = response.text.match(/-?\d+(\.\d+)?/);
                return bindingEnergyText ? parseFloat(bindingEnergyText[0]) : null;
            
            case AgentName.SYNTHESIZABILITY:
                response = await ai.models.generateContent({
                    model,
                    contents: `Synthesizability Agent: For the molecule with SMILES string "${prompt}", calculate its Synthetic Accessibility (SA) Score using established cheminformatics principles (e.g., based on fragment complexity and stereocenters). Provide a single numerical score between 1 (very easy to make) and 10 (very difficult to make).`,
                    config: { thinkingConfig: { thinkingBudget: 2048 } }
                });
                const saScoreText = response.text.match(/-?\d+(\.\d+)?/);
                return saScoreText ? parseFloat(saScoreText[0]) : null;
            
            case AgentName.INTERACTION_ANALYSIS:
                const { smiles, pdbId } = JSON.parse(prompt);
                 response = await ai.models.generateContent({
                    model,
                    contents: `Interaction Analysis Agent: Given the protein PDB ID "${pdbId}" and the ligand SMILES string "${smiles}", identify the key interacting amino acid residues within a 5 angstrom radius. Specifically list all Hydrogen Bonds (with distance), Hydrophobic interactions, and Pi-Stacking interactions. For each interaction, provide the 1-based indices of the atoms involved for both the ligand and the protein. Output ONLY a JSON array of Interaction objects.`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: interactionSchema,
                        thinkingConfig: { thinkingBudget: 8192 }
                    }
                });
                return JSON.parse(response.text);

            case AgentName.RETROSYNTHESIS:
                response = await ai.models.generateContent({
                    model,
                    contents: `Retrosynthesis Agent: For the molecule with SMILES string "${prompt}", predict a viable, high-level synthetic pathway. Provide a step-by-step reaction plan. Output as a JSON array of strings, where each string is a single step.`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: {
                            type: Type.ARRAY,
                            items: { type: Type.STRING }
                        },
                        thinkingConfig: { thinkingBudget: 8192 }
                    }
                });
                return JSON.parse(response.text);
            
             case AgentName.FAILURE_ANALYSIS:
                response = await ai.models.generateContent({
                    model,
                    contents: `Failure Analysis Agent: ${prompt}`,
                    config: {
                        thinkingConfig: { thinkingBudget: 4096 }
                    }
                });
                return response.text;

            case AgentName.HYPOTHESIS:
                 response = await ai.models.generateContent({
                    model,
                    contents: `Hypothesis Agent: ${prompt}`,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: {
                            type: Type.ARRAY,
                            items: { type: Type.STRING }
                        },
                        thinkingConfig: { thinkingBudget: 4096 }
                    }
                });
                return JSON.parse(response.text);

            default:
                throw new Error(`Agent ${agentName} not implemented`);
        }
    } catch (error) {
        console.error(`Error in ${agentName}:`, error);
        updateStatus(agentName, AgentStatus.ERROR, `Error in ${agentName}. See console for details.`);
        return null;
    }
};

export const runFullWorkflow = async (
    prompt: string,
    updateStatus: (agent: AgentName, status: AgentStatus, message: string) => void
): Promise<ResultData> => {
    const finalResult: ResultData = {
        summary: "",
        molecules: [],
        literature: [],
        experimentalPlan: [],
        retrosynthesisPlan: [],
        knowledgeGraphUpdate: { nodes: [], edges: [] },
        proactiveSuggestions: [],
    };
    
    // 0. Target ID Agent
    updateStatus(AgentName.TARGET_IDENTIFICATION, AgentStatus.WORKING, "Identifying protein target...");
    const targetResult = await runAgent(AgentName.TARGET_IDENTIFICATION, prompt, updateStatus);
    finalResult.pdbId = targetResult.pdbId;
    const pdbIdString = finalResult.pdbId ? `(PDB ID: ${finalResult.pdbId})` : '(No PDB ID found)';
    updateStatus(AgentName.TARGET_IDENTIFICATION, AgentStatus.DONE, `Target identification complete. ${pdbIdString}`);


    // 1. Literature Agent
    updateStatus(AgentName.LITERATURE, AgentStatus.WORKING, "Searching literature...");
    const litResult = await runAgent(AgentName.LITERATURE, prompt, updateStatus);
    const litSummary = litResult.text;
    if(litResult.groundingChunks) {
        finalResult.literature = litResult.groundingChunks
            .map((chunk: any) => ({
                title: chunk.web?.title || 'Untitled',
                url: chunk.web?.uri || '#',
                summary: `Source from ${chunk.web?.uri || 'web'}`
            }))
            .slice(0, 3); // Take top 3
    }
    updateStatus(AgentName.LITERATURE, AgentStatus.DONE, "Literature review complete.");
    const designPromptContext = `${prompt}. Protein Target: ${pdbIdString}. Literature context: ${litSummary}`;

    // 2. Molecular Design Agent
    const designPrompt = `Based on the goal "${designPromptContext}", generate 3 novel molecule candidates. Output as a JSON array.`;
    updateStatus(AgentName.MOLECULAR_DESIGN, AgentStatus.WORKING, "Generating candidates...");
    const designedMolecules: Molecule[] = await runAgent(AgentName.MOLECULAR_DESIGN, designPrompt, updateStatus);
    finalResult.molecules = designedMolecules;
    updateStatus(AgentName.MOLECULAR_DESIGN, AgentStatus.DONE, `${designedMolecules.length} candidates generated.`);

    // 3. ADMET, Quantum & Synthesizability Agents (run in parallel for each molecule)
    updateStatus(AgentName.PROPERTY_PREDICTION, AgentStatus.WORKING, "Predicting properties for candidates...");
    updateStatus(AgentName.QUANTUM_SIMULATION, AgentStatus.WORKING, "Running quantum simulations...");
    updateStatus(AgentName.SYNTHESIZABILITY, AgentStatus.WORKING, "Analyzing synthetic accessibility...");

    await Promise.all(finalResult.molecules.map(async (molecule, index) => {
        const properties = await runAgent(AgentName.PROPERTY_PREDICTION, molecule.smiles, updateStatus);
        molecule.admet = properties?.admet;
        molecule.painsAlerts = properties?.painsAlerts;
        molecule.bindingEnergy = await runAgent(AgentName.QUANTUM_SIMULATION, molecule.smiles, updateStatus);
        molecule.saScore = await runAgent(AgentName.SYNTHESIZABILITY, molecule.smiles, updateStatus);

        const progressMessage = `Analyzed molecule ${index + 1}/${finalResult.molecules.length}`;
        updateStatus(AgentName.PROPERTY_PREDICTION, AgentStatus.WORKING, progressMessage);
        updateStatus(AgentName.QUANTUM_SIMULATION, AgentStatus.WORKING, progressMessage);
        updateStatus(AgentName.SYNTHESIZABILITY, AgentStatus.WORKING, progressMessage);
    }));
    updateStatus(AgentName.PROPERTY_PREDICTION, AgentStatus.DONE, "Property prediction complete.");
    updateStatus(AgentName.QUANTUM_SIMULATION, AgentStatus.DONE, "Quantum simulations complete.");
    updateStatus(AgentName.SYNTHESIZABILITY, AgentStatus.DONE, "Synthesis analysis complete.");

    // Sort molecules by binding energy (more negative is better)
    finalResult.molecules.sort((a, b) => (a.bindingEnergy || 0) - (b.bindingEnergy || 0));
    
    let bestCandidate = finalResult.molecules[0];
    
    if (!bestCandidate) {
        throw new Error("Workflow failed: No candidate molecules were generated.");
    }

    // 4. Interaction Analysis for the best candidate
    if (bestCandidate && finalResult.pdbId) {
        updateStatus(AgentName.INTERACTION_ANALYSIS, AgentStatus.WORKING, "Analyzing binding site interactions...");
        const interactionPrompt = JSON.stringify({ smiles: bestCandidate.smiles, pdbId: finalResult.pdbId });
        bestCandidate.interactions = await runAgent(AgentName.INTERACTION_ANALYSIS, interactionPrompt, updateStatus);
        finalResult.molecules[0] = bestCandidate;
        updateStatus(AgentName.INTERACTION_ANALYSIS, AgentStatus.DONE, "Interaction analysis complete.");
    }

    // 5. Failure Analysis Agent (if results are suboptimal)
    const isSuboptimal = !bestCandidate || (bestCandidate.bindingEnergy ?? 0) > -20 || (bestCandidate.admet?.toxicity.score ?? 0) > 0.7;
    if (isSuboptimal) {
        updateStatus(AgentName.FAILURE_ANALYSIS, AgentStatus.WORKING, "Analyzing suboptimal results...");
        const failurePrompt = `The drug discovery workflow produced suboptimal results for the query: "${prompt}".
        The best candidate found was "${bestCandidate?.name}" with Binding Energy: ${bestCandidate?.bindingEnergy?.toFixed(2)} kJ/mol and a Toxicity Score of ${bestCandidate?.admet?.toxicity.score?.toFixed(2)}.
        Literature context: ${litSummary}.
        Hypothesize why the initial design failed to produce a strong candidate and suggest a revised, high-level strategy. For example, should the chemical space be expanded, is the target particularly difficult, or should alternative scaffolds be considered? Provide a concise report.`;
        
        const failureReport = await runAgent(AgentName.FAILURE_ANALYSIS, failurePrompt, updateStatus);
        finalResult.failureAnalysisReport = failureReport;
        updateStatus(AgentName.FAILURE_ANALYSIS, AgentStatus.DONE, "Failure analysis complete.");
    }

    // 6. Retrosynthesis Agent for the best candidate
    if (bestCandidate) {
        updateStatus(AgentName.RETROSYNTHESIS, AgentStatus.WORKING, "Predicting synthesis pathway...");
        const retrosynthesisPlan = await runAgent(AgentName.RETROSYNTHESIS, bestCandidate.smiles, updateStatus);
        finalResult.retrosynthesisPlan = retrosynthesisPlan;
        updateStatus(AgentName.RETROSYNTHESIS, AgentStatus.DONE, "Synthesis plan generated.");
    }


    // 7. Experimental Planner & Knowledge Graph Agents
    const failureReportContext = finalResult.failureAnalysisReport ? `A failure analysis was conducted, which concluded: "${finalResult.failureAnalysisReport}"` : "";
    const finalPrompt = `Initial query: "${prompt}".
    Top candidate: ${bestCandidate.name} (SMILES: ${bestCandidate.smiles})
    Protein Target: ${pdbIdString}
    ADMET: ${JSON.stringify(bestCandidate.admet)}
    Binding Energy: ${bestCandidate.bindingEnergy} kJ/mol
    Literature Context: ${litSummary}
    ${failureReportContext}
    
    Generate a JSON output with:
    1. 'summary': A concise summary of the process and the lead candidate's potential. If a failure analysis was done, incorporate its findings into the summary.
    2. 'experimentalPlan': A step-by-step plan to synthesize and validate this candidate.
    3. 'knowledgeGraphUpdate': A graph object with nodes (candidate, target, 2-3 concepts) and edges connecting them.`;

    updateStatus(AgentName.EXPERIMENTAL_PLANNER, AgentStatus.WORKING, "Generating experimental plan...");
    updateStatus(AgentName.KNOWLEDGE_GRAPH, AgentStatus.WORKING, "Updating knowledge graph...");

    const finalResponse = await ai.models.generateContent({
        model,
        contents: finalPrompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    summary: { type: Type.STRING },
                    experimentalPlan: { type: Type.ARRAY, items: { type: Type.STRING } },
                    knowledgeGraphUpdate: knowledgeGraphSchema
                },
                required: ['summary', 'experimentalPlan', 'knowledgeGraphUpdate']
            },
            thinkingConfig: { thinkingBudget: 8192 }
        },
    });

    const finalData = JSON.parse(finalResponse.text);
    finalResult.summary = finalData.summary;
    finalResult.experimentalPlan = finalData.experimentalPlan;
    finalResult.knowledgeGraphUpdate = finalData.knowledgeGraphUpdate;

    updateStatus(AgentName.EXPERIMENTAL_PLANNER, AgentStatus.DONE, "Experimental plan generated.");
    updateStatus(AgentName.KNOWLEDGE_GRAPH, AgentStatus.DONE, "Knowledge graph updated.");
    
    // 8. Hypothesis Agent
    updateStatus(AgentName.HYPOTHESIS, AgentStatus.WORKING, "Generating next steps...");
    const hypothesisPrompt = `Based on the full results of this drug discovery run (Lead candidate: ${bestCandidate.name}, Binding Energy: ${bestCandidate.bindingEnergy}, ADMET: ${JSON.stringify(bestCandidate.admet)}), generate 2-3 actionable, concise suggestions for the next refinement step. If a failure analysis was conducted (${!!finalResult.failureAnalysisReport}), make the suggestions strategic to address the failure. Frame them as commands. For example: "Expand search to a different chemical class based on patent XYZ" or "Replace the nitro group with a bioisostere to reduce toxicity". Output as a JSON array of strings.`;
    const suggestions = await runAgent(AgentName.HYPOTHESIS, hypothesisPrompt, updateStatus);
    finalResult.proactiveSuggestions = suggestions;
    updateStatus(AgentName.HYPOTHESIS, AgentStatus.DONE, "Suggestions generated.");


    return finalResult;
};

export const runRefinementWorkflow = async (
    refinementPrompt: string,
    previousData: ResultData,
    updateStatus: (agent: AgentName, status: AgentStatus, message: string) => void
): Promise<ResultData> => {
    // 1. Get the lead candidate to modify
    const leadCandidate = previousData.molecules[0];
    if (!leadCandidate) throw new Error("No lead candidate to refine.");

    // 2. Run Molecular Design Agent for modification
    updateStatus(AgentName.MOLECULAR_DESIGN, AgentStatus.WORKING, 'Refining lead candidate...');
    const designPrompt = `Based on the molecule "${leadCandidate.name}" (SMILES: ${leadCandidate.smiles}), generate ONE new molecule that addresses this user request: "${refinementPrompt}". Output as a JSON array with one molecule.`;
    const newMolecules: Molecule[] = await runAgent(AgentName.MOLECULAR_DESIGN, designPrompt, updateStatus);
    if (!newMolecules || newMolecules.length === 0) throw new Error("Refinement did not produce a new molecule.");
    const refinedMolecule = newMolecules[0];
    updateStatus(AgentName.MOLECULAR_DESIGN, AgentStatus.DONE, `New candidate ${refinedMolecule.name} generated.`);

    // 3. Analyze the new molecule
    updateStatus(AgentName.PROPERTY_PREDICTION, AgentStatus.WORKING, `Analyzing ${refinedMolecule.name}...`);
    updateStatus(AgentName.QUANTUM_SIMULATION, AgentStatus.WORKING, `Simulating ${refinedMolecule.name}...`);
    updateStatus(AgentName.SYNTHESIZABILITY, AgentStatus.WORKING, "Analyzing synthetic accessibility...");
    
    const properties = await runAgent(AgentName.PROPERTY_PREDICTION, refinedMolecule.smiles, updateStatus);
    refinedMolecule.admet = properties?.admet;
    refinedMolecule.painsAlerts = properties?.painsAlerts;
    refinedMolecule.bindingEnergy = await runAgent(AgentName.QUANTUM_SIMULATION, refinedMolecule.smiles, updateStatus);
    refinedMolecule.saScore = await runAgent(AgentName.SYNTHESIZABILITY, refinedMolecule.smiles, updateStatus);
    
    updateStatus(AgentName.PROPERTY_PREDICTION, AgentStatus.DONE, "Analysis complete.");
    updateStatus(AgentName.QUANTUM_SIMULATION, AgentStatus.DONE, "Simulation complete.");
    updateStatus(AgentName.SYNTHESIZABILITY, AgentStatus.DONE, "Synthesis analysis complete.");


    // 4. Combine and re-sort results
    const allMolecules = [...previousData.molecules, refinedMolecule];
    allMolecules.sort((a, b) => (a.bindingEnergy || 0) - (b.bindingEnergy || 0));
    let newLeadCandidate = allMolecules[0];

    // 5. Interaction Analysis for the NEW lead if it changed
    if (newLeadCandidate.smiles !== leadCandidate.smiles && previousData.pdbId) {
        updateStatus(AgentName.INTERACTION_ANALYSIS, AgentStatus.WORKING, "Analyzing new lead's interactions...");
        const interactionPrompt = JSON.stringify({ smiles: newLeadCandidate.smiles, pdbId: previousData.pdbId });
        newLeadCandidate.interactions = await runAgent(AgentName.INTERACTION_ANALYSIS, interactionPrompt, updateStatus);
        updateStatus(AgentName.INTERACTION_ANALYSIS, AgentStatus.DONE, "Interaction analysis complete.");
    } else {
        newLeadCandidate.interactions = leadCandidate.interactions; // Carry over old interactions if lead is the same
    }

    const updatedResultData: ResultData = {
        ...previousData,
        molecules: allMolecules,
        failureAnalysisReport: undefined, // Clear any previous failure report
    };
    
    // 6. Update Retrosynthesis for the *new* lead if it changed
    if (newLeadCandidate.smiles !== leadCandidate.smiles) {
        updateStatus(AgentName.RETROSYNTHESIS, AgentStatus.WORKING, "Updating synthesis for new lead...");
        const retrosynthesisPlan = await runAgent(AgentName.RETROSYNTHESIS, newLeadCandidate.smiles, updateStatus);
        updatedResultData.retrosynthesisPlan = retrosynthesisPlan;
        updateStatus(AgentName.RETROSYNTHESIS, AgentStatus.DONE, "Synthesis plan updated.");
    } else {
         updateStatus(AgentName.RETROSYNTHESIS, AgentStatus.DONE, "Synthesis plan for lead is unchanged.");
    }

    // 7. Update Summary, Plan, and Knowledge Graph
    const finalPrompt = `This is a refinement run.
    Previous lead: ${leadCandidate.name} (Binding Energy: ${leadCandidate.bindingEnergy?.toFixed(2)} kJ/mol).
    User request: "${refinementPrompt}".
    New candidate generated: ${refinedMolecule.name} (Binding Energy: ${refinedMolecule.bindingEnergy?.toFixed(2)} kJ/mol).
    The NEW top candidate is now: ${newLeadCandidate.name} (SMILES: ${newLeadCandidate.smiles}, Binding Energy: ${newLeadCandidate.bindingEnergy?.toFixed(2)} kJ/mol, ADMET: ${JSON.stringify(newLeadCandidate.admet)}).
    
    Generate an updated JSON output with:
    1. 'summary': A new summary explaining the refinement, its result, and the new lead's potential.
    2. 'experimentalPlan': An updated plan for the NEW lead candidate.
    3. 'knowledgeGraphUpdate': An updated graph incorporating the new candidate and its relationship to the previous lead and target.`;

    updateStatus(AgentName.EXPERIMENTAL_PLANNER, AgentStatus.WORKING, "Updating experimental plan...");
    updateStatus(AgentName.KNOWLEDGE_GRAPH, AgentStatus.WORKING, "Updating knowledge graph...");

    const finalResponse = await ai.models.generateContent({
        model,
        contents: finalPrompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    summary: { type: Type.STRING },
                    experimentalPlan: { type: Type.ARRAY, items: { type: Type.STRING } },
                    knowledgeGraphUpdate: knowledgeGraphSchema
                },
                required: ['summary', 'experimentalPlan', 'knowledgeGraphUpdate']
            },
            thinkingConfig: { thinkingBudget: 8192 }
        },
    });

    const finalData = JSON.parse(finalResponse.text);
    updatedResultData.summary = finalData.summary;
    updatedResultData.experimentalPlan = finalData.experimentalPlan;
    updatedResultData.knowledgeGraphUpdate = finalData.knowledgeGraphUpdate;

    updateStatus(AgentName.EXPERIMENTAL_PLANNER, AgentStatus.DONE, "Experimental plan updated.");
    updateStatus(AgentName.KNOWLEDGE_GRAPH, AgentStatus.DONE, "Knowledge graph updated.");
    
    // 8. Hypothesis Agent for the refinement
    updateStatus(AgentName.HYPOTHESIS, AgentStatus.WORKING, "Generating next steps...");
    const hypothesisPrompt = `Based on the results of this REFINEMENT run (New lead candidate: ${newLeadCandidate.name}, Binding Energy: ${newLeadCandidate.bindingEnergy}, ADMET: ${JSON.stringify(newLeadCandidate.admet)}), generate 2-3 new, actionable suggestions for the next refinement step. Frame them as commands. Output as a JSON array of strings.`;
    const suggestions = await runAgent(AgentName.HYPOTHESIS, hypothesisPrompt, updateStatus);
    updatedResultData.proactiveSuggestions = suggestions;
    updateStatus(AgentName.HYPOTHESIS, AgentStatus.DONE, "Suggestions generated.");


    return updatedResultData;
}

// --- Voice Conversation Service ---

export const runHypothesisOnTranscript = async (
    resultData: ResultData,
    transcript: string,
    updateStatus: (agent: AgentName, status: AgentStatus, message: string) => void
): Promise<string[]> => {
    const hypothesisPrompt = `Based on the full results of a previous drug discovery run AND the content of a follow-up voice discussion, generate 2-3 new, actionable, and concise suggestions for the next refinement step. Frame them as commands.

    **Previous Results Context:**
    - Summary: ${resultData.summary}
    - Lead Candidate: ${resultData.molecules[0]?.name} (Binding Energy: ${resultData.molecules[0]?.bindingEnergy?.toFixed(2)} kJ/mol)
    
    **Follow-up Voice Discussion Transcript:**
    ${transcript}

    Generate suggestions that intelligently combine insights from both the original data and the new conversation. For example, if the user expressed concern about solubility in the call, suggest modifications to improve it. Output as a JSON array of strings.`;
    
    const suggestions = await runAgent(AgentName.HYPOTHESIS, hypothesisPrompt, updateStatus);
    updateStatus(AgentName.HYPOTHESIS, AgentStatus.DONE, "New suggestions generated from discussion.");
    return suggestions;
};


// Base64 encoding/decoding and audio buffer functions as per Gemini Live API guidelines.
function encode(bytes: Uint8Array) {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// Fix: Export the decode function so it can be imported and used in App.tsx callbacks.
export function decode(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

export async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

// Fix: Export the createBlob function so it can be imported and used in App.tsx callbacks.
export function createBlob(data: Float32Array): Blob {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    int16[i] = data[i] * 32768;
  }
  return {
    data: encode(new Uint8Array(int16.buffer)),
    mimeType: 'audio/pcm;rate=16000',
  };
}

export interface VoiceCallbacks {
    onopen: () => void;
    onmessage: (message: LiveServerMessage) => Promise<void>;
    onerror: (e: ErrorEvent) => void;
    onclose: (e: CloseEvent) => void;
}

export const startVoiceConversation = (
    resultData: ResultData,
    callbacks: VoiceCallbacks
) => {
    const leadCandidate = resultData.molecules[0];
    const systemInstruction = `You are Milimo, an AI Co-Scientist, in a real-time voice call with a researcher. Your goal is to discuss the results of a recent drug discovery workflow. The researcher may ask questions about the findings. Be helpful, conversational, and concise.

Key context from the results:
- Executive Summary: "${resultData.summary}"
- Lead Candidate Molecule: "${leadCandidate.name}"
- Lead Candidate Binding Energy: ${leadCandidate.bindingEnergy?.toFixed(2)} kJ/mol
- Lead Candidate Toxicity Score: ${leadCandidate.admet?.toxicity.score?.toFixed(2)} (where a higher score is worse).

Engage in a scientific conversation based on this context.`;

    const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        callbacks,
        config: {
            responseModalities: [Modality.AUDIO],
            speechConfig: {
                voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } },
            },
            inputAudioTranscription: {},
            outputAudioTranscription: {},
            systemInstruction,
        },
    });
    
    // Fix: Remove createBlob and decode from the return value to avoid scoping issues in App.tsx.
    // They are now exported and can be imported directly.
    return { sessionPromise };
};
