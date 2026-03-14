import { useState, useRef, useEffect } from 'react';
import { fetchWithAuth } from '../../services/api';
import { extensionSessionStore } from '../../services/sessionStore';
import type { AppState, Session, Agent } from './types';
import { AgentStatus, AgentName } from './types';
import MoleculeViewer3D from './components/MoleculeViewer3D';
import KnowledgeGraph from './components/KnowledgeGraph';
import CandidateComparisonChart from './components/CandidateComparisonChart';
import ADMETHeatmap from './components/ADMETHeatmap';
import { 
    SendIcon, LoaderIcon, 
    BeakerIcon, BookOpenIcon, AtomIcon, ZapIcon, ListChecksIcon, Share2Icon, 
    ClipboardListIcon, FlaskConicalIcon, CrosshairIcon, 
    NetworkIcon, LightbulbIcon, AlertTriangleIcon, FileIcon, DownloadIcon, 
    PlusCircleIcon 
} from './components/Icons';

interface DrugDiscoveryPanelProps {
    instanceId: string;
    isOpen: boolean;
    onClose: () => void;
    currentConversationId?: string;
    onLoadConversation?: (id: string) => void;
}

const initialAgents: Agent[] = [
    { name: AgentName.TARGET_IDENTIFICATION, status: AgentStatus.IDLE, description: "Identifies protein target from prompt." },
    { name: AgentName.LITERATURE, status: AgentStatus.IDLE, description: "Scans scientific literature for insights." },
    { name: AgentName.MOLECULAR_DESIGN, status: AgentStatus.IDLE, description: "Generates novel molecular structures." },
    { name: AgentName.PROPERTY_PREDICTION, status: AgentStatus.IDLE, description: "Predicts ADMET properties of molecules." },
    { name: AgentName.QUANTUM_SIMULATION, status: AgentStatus.IDLE, description: "Simulates molecular binding energy." },
    { name: AgentName.SYNTHESIZABILITY, status: AgentStatus.IDLE, description: "Calculates synthetic accessibility score." },
    { name: AgentName.INTERACTION_ANALYSIS, status: AgentStatus.IDLE, description: "Analyzes ligand-protein interactions." },
    { name: AgentName.RETROSYNTHESIS, status: AgentStatus.IDLE, description: "Predicts chemical synthesis pathway." },
    { name: AgentName.EXPERIMENTAL_PLANNER, status: AgentStatus.IDLE, description: "Designs validation experiments." },
    { name: AgentName.KNOWLEDGE_GRAPH, status: AgentStatus.IDLE, description: "Integrates findings into a knowledge base." },
    { name: AgentName.FAILURE_ANALYSIS, status: AgentStatus.IDLE, description: "Analyzes workflow failures." },
    { name: AgentName.HYPOTHESIS, status: AgentStatus.IDLE, description: "Generates proactive next steps." },
];

export function DrugDiscoveryPanel({ instanceId, isOpen, onClose, currentConversationId }: DrugDiscoveryPanelProps) {
    const [state, setState] = useState<AppState>({
        agents: initialAgents,
        messages: [],
        isLoading: false,
        resultData: null,
        activeTab: 'dashboard',
        selectedMolecule: null,
        uploadedFile: null,
        history: [],
        activeSessionId: `session-${Date.now()}`,
    });

    const [inputValue, setInputValue] = useState('');
    const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
    const [isRefinementMode, setIsRefinementMode] = useState(false);
    const [analysisView, setAnalysisView] = useState<'chart' | 'heatmap'>('chart');
    const [basisSet, setBasisSet] = useState<'sto3g' | '631g'>('sto3g');
    const logsEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Persistence & History: Load on mount
    useEffect(() => {
        const savedHistory = localStorage.getItem('mqdd_history');
        if (savedHistory) {
            try {
                const historyData = JSON.parse(savedHistory);
                setState(s => ({ ...s, history: historyData }));
            } catch (e) {
                console.error("Failed to parse history", e);
            }
        }

        const savedSession = extensionSessionStore.get<any>(instanceId);
        if (savedSession) {
            setState(s => ({ ...s, ...savedSession }));
        } else if (currentConversationId) {
            const fetchLatest = async () => {
                try {
                    const res = await fetchWithAuth(`/api/mqdd/results/${currentConversationId}`, {
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    });
                    const data = await res.json();
                    if (data && !data.error) {
                        setState(s => ({
                            ...s,
                            resultData: data,
                            selectedMolecule: data.molecules?.[0] || null,
                            activeTab: 'dashboard'
                        }));
                    }
                } catch (e) {
                    console.error("Failed to load previous MQDD results", e);
                }
            };
            fetchLatest();
        }
    }, [instanceId, currentConversationId]);

    // Persistence: Save on change
    useEffect(() => {
        extensionSessionStore.set(instanceId, {
            agents: state.agents,
            messages: state.messages,
            resultData: state.resultData,
            activeTab: state.activeTab,
            selectedMolecule: state.selectedMolecule,
            activeSessionId: state.activeSessionId
        });
    }, [instanceId, state]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [state.messages]);

    const handleRunWorkflow = async (promptOverride?: string) => {
        const query = promptOverride || inputValue;
        if (!query.trim()) return;

        setState(s => ({
            ...s,
            isLoading: true,
            messages: [...s.messages, { id: Date.now().toString(), sender: 'user', text: query }],
            agents: initialAgents.map(a => ({ ...a, status: AgentStatus.IDLE, message: 'Queued' })),
            resultData: null,
            selectedMolecule: null,
            activeSessionId: s.activeSessionId || Date.now().toString()
        }));
        setInputValue('');

        try {
            const response = await fetchWithAuth('/api/mqdd/workflow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    prompt: isRefinementMode ? `Refine results for: ${query}` : query, 
                    conversation_id: currentConversationId,
                    basis: basisSet,
                    pdb_content: state.uploadedFile?.content || null
                })
            });

            if (!response.body) throw new Error("Stream not available");
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const part of parts) {
                    if (part.startsWith('event: ')) {
                        const eventMatch = part.match(/event: (.*)\ndata: (.*)/s);
                        if (eventMatch) {
                            const eventType = eventMatch[1];
                            const data = JSON.parse(eventMatch[2]);

                            if (eventType === 'status') {
                                setState(s => ({
                                    ...s,
                                    agents: s.agents.map(a => {
                                        const backendKey = data.agent as keyof typeof AgentName;
                                        const mappedName = AgentName[backendKey] || data.agent;
                                        return a.name === mappedName ? { ...a, status: data.status.toLowerCase() as AgentStatus, message: data.message } : a;
                                    })
                                }));
                            } else if (eventType === 'result') {
                                setState(s => {
                                    const finalMessages = [...s.messages, { id: Date.now().toString(), sender: 'ai' as const, text: 'Discovery workflow complete. Analysis results are now available in the explorer.', data }];
                                    const newHistory = [...s.history];
                                    const sessionName = data.molecules?.[0]?.name || query.substring(0, 30);
                                    
                                    const fullSession: Session = {
                                        id: s.activeSessionId,
                                        name: sessionName,
                                        timestamp: Date.now(),
                                        messages: finalMessages,
                                        resultData: data,
                                        agents: s.agents
                                    };

                                    const sessionIndex = newHistory.findIndex(h => h.id === s.activeSessionId);
                                    if (sessionIndex >= 0) {
                                        newHistory[sessionIndex] = fullSession;
                                    } else {
                                        newHistory.unshift(fullSession);
                                    }
                                    
                                    localStorage.setItem('mqdd_history', JSON.stringify(newHistory));
                                    
                                    return {
                                        ...s,
                                        resultData: data,
                                        selectedMolecule: data.molecules?.[0] || null,
                                        isLoading: false,
                                        activeTab: 'dashboard',
                                        messages: finalMessages,
                                        history: newHistory
                                    };
                                });
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Workflow failed:", error);
            setState(s => ({ ...s, isLoading: false }));
        }
    };

    const handleNewSession = () => {
        const newSessionId = `session-${Date.now()}`;
        setState({
            agents: initialAgents,
            messages: [],
            isLoading: false,
            resultData: null,
            activeTab: 'dashboard',
            selectedMolecule: null,
            uploadedFile: null,
            history: state.history,
            activeSessionId: newSessionId,
        });
    };

    const handleSelectSession = (session: Session) => {
        setState(s => ({
            ...s,
            agents: session.agents,
            messages: session.messages,
            resultData: session.resultData,
            activeTab: 'dashboard',
            selectedMolecule: session.resultData?.molecules?.[0] || null,
            activeSessionId: session.id
        }));
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target?.result as string;
            setState(s => ({ ...s, uploadedFile: { name: file.name, content } }));
            handleRunWorkflow(`Analyze uploaded target file: ${file.name}`);
        };
        reader.readAsText(file);
    };

    const handleExportMarkdown = () => {
        if (!state.resultData) return;
        const lead = state.selectedMolecule || state.resultData.molecules[0];
        let content = `# MQDD Research Report: ${lead.name}\n\n${state.resultData.summary}\n`;
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MQDD_Report_${lead.name.replace(/\s+/g, '_')}.md`;
        a.click();
    };

    const handleExportCSV = () => {
        if (!state.resultData) return;
        const headers = ["Name", "SMILES", "Binding Energy", "SA Score", "LogP", "Permeability", "Toxicity Score"];
        const rows = state.resultData.molecules.map(m => [
            m.name,
            m.smiles,
            m.bindingEnergy,
            m.saScore,
            m.admet?.logP?.value,
            m.admet?.permeability?.value,
            m.admet?.toxicity?.score
        ]);
        const content = [headers, ...rows].map(e => e.join(",")).join("\n");
        const blob = new Blob([content], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MQDD_Candidates_${Date.now()}.csv`;
        a.click();
    };

    const handleExportSDF = async () => {
        if (!state.selectedMolecule) return;
        try {
            const smiles = state.selectedMolecule.smiles;
            const res = await fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/${encodeURIComponent(smiles)}/SDF?record_type=3d`);
            if (!res.ok) throw new Error("Failed to fetch SDF from PubChem");
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${state.selectedMolecule.name}_3D.sdf`;
            a.click();
        } catch (e) {
            console.error("SDF Export failed", e);
            alert("SDF export failed. Please try again later.");
        }
    };

    const AgentIcon = ({ name }: { name: string }) => {
        const className = "w-4 h-4";
        if (name.includes('Target')) return <CrosshairIcon className={className} />;
        if (name.includes('Literature')) return <BookOpenIcon className={className} />;
        if (name.includes('Design')) return <AtomIcon className={className} />;
        if (name.includes('ADMET')) return <BeakerIcon className={className} />;
        if (name.includes('Quantum')) return <ZapIcon className={className} />;
        if (name.includes('Synthesizability')) return <ClipboardListIcon className={className} />;
        if (name.includes('Interaction')) return <NetworkIcon className={className} />;
        if (name.includes('Retrosynthesis')) return <FlaskConicalIcon className={className} />;
        if (name.includes('Planner')) return <ListChecksIcon className={className} />;
        if (name.includes('Graph')) return <Share2Icon className={className} />;
        if (name.includes('Failure')) return <AlertTriangleIcon className={className} />;
        return <LightbulbIcon className={className} />;
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xl animate-fade-in">
            <div className="absolute inset-0" onClick={onClose} />
            
            <div className="relative w-full max-w-[1500px] h-[92vh] flex bg-mq-black border border-mq-border rounded-[2.5rem] overflow-hidden shadow-2xl shadow-mq-cyan/5">
                
                {/* 1. Left Sidebar: Agent Workflow & History */}
                <aside className="w-80 bg-mq-void/50 border-r border-mq-border flex flex-col p-6 overflow-hidden">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="w-12 h-12 rounded-2xl bg-mq-cyan/10 border border-mq-cyan/20 flex items-center justify-center text-2xl shadow-glow-cyan animate-pulse">🧬</div>
                        <div>
                            <h1 className="text-lg font-bold text-mq-text tracking-tight uppercase">Milimo QDD</h1>
                            <p className="text-[10px] text-mq-cyan font-mono tracking-widest uppercase opacity-70">Research Node v2.5</p>
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col min-h-0">
                        <h2 className="text-[10px] font-bold text-mq-text-tertiary uppercase tracking-[0.2em] mb-4">Agent Timeline</h2>
                        
                        <div className="mb-6">
                            <button
                                onClick={() => setIsRefinementMode(!isRefinementMode)}
                                className={`w-full px-4 py-2.5 rounded-xl border text-[11px] font-bold uppercase tracking-widest transition-apple flex items-center justify-center gap-3 ${isRefinementMode ? 'bg-mq-amber/10 border-mq-amber/40 text-mq-amber shadow-glow-amber-subtle' : 'bg-mq-elevated border-mq-border text-mq-text-tertiary hover:bg-mq-surface/50'}`}
                                title="Toggle between discovery and refinement mode"
                            >
                                <ZapIcon className={`w-4 h-4 ${isRefinementMode ? 'animate-pulse' : ''}`} />
                                Mode: {isRefinementMode ? 'Refinement' : 'Discovery'}
                            </button>
                        </div>

                        <div className="mb-8 p-3 rounded-xl bg-mq-void/30 border border-mq-border/50">
                            <h3 className="text-[9px] font-bold text-mq-text-tertiary uppercase tracking-[0.2em] mb-3 px-1">Quantum Engine Basis</h3>
                            <div className="flex gap-1 bg-mq-elevated p-1 rounded-lg border border-mq-border">
                                <button 
                                    onClick={() => setBasisSet('sto3g')} 
                                    className={`flex-1 py-1 text-[10px] font-bold rounded transition-apple ${basisSet === 'sto3g' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                >
                                    STO-3G
                                </button>
                                <button 
                                    onClick={() => setBasisSet('631g')} 
                                    className={`flex-1 py-1 text-[10px] font-bold rounded transition-apple ${basisSet === '631g' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                >
                                    6-31G
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                            <div className="relative pl-10 space-y-6">
                                <div className="absolute left-[20px] top-2 bottom-2 w-[1px] bg-mq-border" />
                                {state.agents.map((agent, i) => (
                                    <div key={i} className="relative flex items-start group">
                                        <div className={`absolute left-[-32px] top-1 w-6 h-6 rounded-full border border-mq-border flex items-center justify-center z-10 transition-apple ${
                                            agent.status === AgentStatus.WORKING ? 'bg-mq-cyan border-mq-cyan shadow-glow-cyan' : 
                                            agent.status === AgentStatus.DONE ? 'bg-mq-teal border-mq-teal' : 'bg-mq-elevated'
                                        }`}>
                                            <AgentIcon name={agent.name} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-center mb-0.5">
                                                <span className={`text-[12px] font-bold ${agent.status === AgentStatus.IDLE ? 'text-mq-text-tertiary' : 'text-mq-text'}`}>{agent.name}</span>
                                                {agent.status === AgentStatus.WORKING && <LoaderIcon className="w-3 h-3 text-mq-cyan animate-spin" />}
                                            </div>
                                            <p className="text-[10px] text-mq-text-tertiary truncate leading-tight">{agent.message || agent.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-6 border-t border-mq-border">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-[10px] font-bold text-mq-text-tertiary uppercase tracking-[0.2em]">Sessions</h2>
                            <button onClick={handleNewSession} className="p-1 hover:text-mq-cyan transition-apple"><PlusCircleIcon className="w-4 h-4" /></button>
                        </div>
                        <div className="space-y-2 h-32 overflow-y-auto custom-scrollbar">
                            {state.history.length === 0 ? (
                                <div className="text-[11px] text-mq-text-tertiary italic text-center py-4 bg-mq-surface/20 rounded-xl border border-mq-border/50">No history yet</div>
                            ) : (
                                state.history.map((s, i) => (
                                    <div key={i} onClick={() => handleSelectSession(s)} className={`p-2 rounded-lg cursor-pointer border transition-apple text-[12px] group ${
                                        state.activeSessionId === s.id ? 'bg-mq-cyan/10 border-mq-cyan/30' : 'hover:bg-mq-surface/50 border-transparent hover:border-mq-border'
                                    }`}>
                                        <div className={`font-medium truncate ${state.activeSessionId === s.id ? 'text-mq-cyan' : 'text-mq-text-secondary group-hover:text-mq-text'}`}>{s.name}</div>
                                        <div className="text-[10px] text-mq-text-tertiary">{new Date(s.timestamp).toLocaleDateString()}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </aside>

                {/* 2. Middle: Interaction Canvas */}
                <main className="flex-1 flex flex-col bg-mq-black overflow-hidden border-r border-mq-border">
                    <div className="flex-1 overflow-y-auto p-12 space-y-8 custom-scrollbar">
                        {!state.resultData && !state.isLoading && (
                            <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto">
                                <div className="w-32 h-32 rounded-[2rem] border border-mq-cyan/30 bg-mq-cyan/5 flex items-center justify-center text-5xl mb-10 shadow-glow-cyan animate-float">⚛️</div>
                                <h3 className="text-3xl font-bold text-mq-text mb-4 tracking-tight">AI Co-Scientist Workspace</h3>
                                <p className="text-mq-text-secondary text-lg leading-relaxed">Initialize discovery protocols by describing your research target. Our multi-agent system will perform literature scans, molecular design, and quantum simulations.</p>
                            </div>
                        )}
                        
                        {state.messages.map((m, i) => (
                            <div key={i} className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}>
                                <div className={`max-w-[80%] p-6 rounded-2xl ${m.sender === 'user' ? 'bg-mq-cyan text-mq-black font-bold' : 'bg-mq-surface/40 border border-mq-border text-mq-text-secondary shadow-lg'}`}>
                                    {m.text}
                                </div>
                            </div>
                        ))}
                        {state.isLoading && (
                            <div className="flex justify-start animate-fade-in">
                                <div className="bg-mq-surface/40 border border-mq-border p-4 rounded-2xl flex gap-2 items-center">
                                    <div className="w-1.5 h-1.5 bg-mq-cyan rounded-full animate-bounce" />
                                    <div className="w-1.5 h-1.5 bg-mq-cyan rounded-full animate-bounce [animation-delay:0.2s]" />
                                    <div className="w-1.5 h-1.5 bg-mq-cyan rounded-full animate-bounce [animation-delay:0.4s]" />
                                </div>
                            </div>
                        )}
                        <div ref={logsEndRef} />
                    </div>

                    <div className="p-10 border-t border-mq-border bg-mq-surface/10 backdrop-blur-md">
                        <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
                        <div className="max-w-4xl mx-auto flex items-center gap-4 bg-mq-surface/30 border border-mq-border rounded-2xl p-2 focus-within:border-mq-cyan transition-apple group">
                            <button onClick={() => fileInputRef.current?.click()} className="p-3 text-mq-text-tertiary hover:text-mq-cyan"><FileIcon className="w-5 h-5" /></button>
                            <input 
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="Design a non-toxic inhibitor for..."
                                className="flex-1 bg-transparent border-none focus:ring-0 text-mq-text placeholder:text-mq-text-tertiary"
                                onKeyDown={(e) => e.key === 'Enter' && handleRunWorkflow(inputValue)}
                            />
                            <button onClick={() => handleRunWorkflow(inputValue)} className="p-3 bg-mq-cyan text-mq-black rounded-xl hover:shadow-glow-cyan transition-apple">
                                <SendIcon className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </main>

                {/* 3. Right Sidebar: Results Explorer */}
                <aside className="w-[480px] bg-mq-void/50 flex flex-col overflow-hidden">
                    <div className="p-6 border-b border-mq-border flex justify-between items-center bg-mq-surface/30">
                        <h2 className="text-sm font-bold text-mq-text uppercase tracking-widest">Results Explorer</h2>
                        <div className="flex gap-2">
                             <button className="p-2 hover:bg-mq-surface/50 rounded-lg text-mq-text-tertiary transition-apple relative" onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}>
                                <DownloadIcon className="w-4 h-4" />
                                {isExportMenuOpen && (
                                    <div className="absolute right-0 top-full mt-2 w-48 bg-mq-elevated border border-mq-border rounded-xl shadow-2xl z-50 overflow-hidden animate-fade-in">
                                        <button onClick={handleExportMarkdown} className="w-full text-left px-5 py-3 hover:bg-mq-cyan/10 text-[12px] text-mq-text border-b border-mq-border last:border-0">Export Summary (.md)</button>
                                        <button onClick={handleExportCSV} className="w-full text-left px-5 py-3 hover:bg-mq-cyan/10 text-[12px] text-mq-text border-b border-mq-border last:border-0">Export Candidates (.csv)</button>
                                        <button onClick={handleExportSDF} className="w-full text-left px-5 py-3 hover:bg-mq-cyan/10 text-[12px] text-mq-text">Export 3D Lead (.sdf)</button>
                                    </div>
                                )}
                            </button>
                            <button onClick={onClose} className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-lg text-mq-text-tertiary transition-apple">✕</button>
                        </div>
                    </div>

                    {!state.resultData ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
                            <div className="w-16 h-16 rounded-full border border-mq-border flex items-center justify-center text-2xl mb-4 opacity-20">📊</div>
                            <p className="text-mq-text-tertiary italic text-sm">Initialize workflow to generate data matrix.</p>
                        </div>
                    ) : (
                        <>
                            <nav className="p-2 bg-mq-black/40 border-b border-mq-border flex flex-wrap gap-1">
                                <div className="flex bg-mq-elevated p-1 rounded-xl border border-mq-border overflow-x-auto custom-scrollbar no-scrollbar scroll-smooth">
                                <button onClick={() => setState(s => ({...s, activeTab: 'dashboard'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'dashboard' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Dashboard</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'lead'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'lead' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Lead</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'analysis'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'analysis' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Analysis</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'synthesis'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'synthesis' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Synthesis</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'plan'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'plan' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Plan</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'knowledge'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'knowledge' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Knowledge</button>
                                <button onClick={() => setState(s => ({...s, activeTab: 'literature'}))} className={`px-5 py-2 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-apple whitespace-nowrap ${state.activeTab === 'literature' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan-subtle' : 'text-mq-text-tertiary hover:text-mq-text hover:bg-mq-surface/50'}`}>Literature</button>
                            </div>
                            </nav>

                            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-8 animate-fade-in content-fade-in">
                                {state.activeTab === 'dashboard' && (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                        <div className="p-6 border border-mq-border rounded-2xl bg-mq-surface/30 shadow-sm border-l-4 border-l-mq-cyan">
                                            <h3 className="text-[11px] font-bold text-mq-cyan uppercase tracking-widest mb-4">Executive Summary</h3>
                                            <p className="text-mq-text-secondary text-[14px] leading-relaxed selection:bg-mq-cyan/20 whitespace-pre-wrap">{state.resultData.summary}</p>
                                        </div>

                                        {state.resultData.proactiveSuggestions && (
                                            <div className="space-y-4">
                                                <h3 className="text-[10px] font-bold text-mq-text-tertiary uppercase tracking-[0.2em]">Proactive Next Steps</h3>
                                                <div className="grid grid-cols-1 gap-3">
                                                    {state.resultData.proactiveSuggestions.map((s, i) => (
                                                        <div key={i} onClick={() => handleRunWorkflow(s)} className="p-4 bg-mq-surface/10 border border-mq-border rounded-xl cursor-pointer hover:border-mq-cyan/40 hover:bg-mq-cyan/5 transition-apple flex items-center gap-4 group">
                                                            <div className="w-8 h-8 rounded-lg bg-mq-elevated flex items-center justify-center group-hover:bg-mq-cyan group-hover:text-mq-black transition-apple">
                                                                <LightbulbIcon className="w-4 h-4" />
                                                            </div>
                                                            <p className="text-[13px] text-mq-text-secondary">{s}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {state.activeTab === 'lead' && state.selectedMolecule && (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                        <div className="grid grid-cols-1 gap-6">
                                            <div className="p-6 border border-mq-border rounded-2xl bg-mq-surface/30">
                                                <div className="flex justify-between items-start mb-6">
                                                    <div className="min-w-0">
                                                        <h3 className="text-xl font-bold text-mq-text truncate">{state.selectedMolecule.name}</h3>
                                                        <p className="text-[10px] font-mono text-mq-cyan mt-1 break-all opacity-60 tracking-tighter">{state.selectedMolecule.smiles}</p>
                                                    </div>
                                                    <div className="flex-shrink-0 px-2 py-1 rounded bg-mq-teal/10 border border-mq-teal/20 text-[9px] font-bold text-mq-teal uppercase shadow-glow-teal-subtle">Lead</div>
                                                </div>

                                                <div className="aspect-square mb-6 rounded-xl overflow-hidden border border-mq-border bg-mq-void/40 flex items-center justify-center p-4">
                                                    <MoleculeViewer3D 
                                                        smiles={state.selectedMolecule.smiles} 
                                                        pdbId={state.resultData.pdbId}
                                                        interactions={state.selectedMolecule.interactions}
                                                        className="w-full h-full"
                                                    />
                                                </div>

                                                <div className="grid grid-cols-2 gap-4">
                                                    <div className="p-4 bg-mq-surface/20 rounded-xl border border-mq-border text-center group hover:border-mq-green/40 transition-apple">
                                                        <div className="text-[9px] font-bold text-mq-text-tertiary uppercase mb-1">Binding Energy</div>
                                                        <div className="text-lg font-bold text-mq-green">{state.selectedMolecule.bindingEnergy?.toFixed(2)} <span className="text-[10px] font-normal text-mq-text-tertiary uppercase">kJ/mol</span></div>
                                                    </div>
                                                    <div className="p-4 bg-mq-surface/20 rounded-xl border border-mq-border text-center group hover:border-mq-cyan/40 transition-apple">
                                                        <div className="text-[9px] font-bold text-mq-text-tertiary uppercase mb-1">SA Score</div>
                                                        <div className="text-lg font-bold text-mq-cyan">{state.selectedMolecule.saScore?.toFixed(2)}</div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="p-6 border border-mq-border rounded-2xl bg-mq-surface/30">
                                                <h3 className="text-[11px] font-bold text-mq-text-tertiary uppercase tracking-widest mb-6">ADMET Property Matrix</h3>
                                                <div className="space-y-6">
                                                    {Object.entries(state.selectedMolecule.admet || {}).map(([key, value]) => {
                                                        const val = value as any;
                                                        return (
                                                            <div key={key} className="group">
                                                                <div className="flex justify-between items-center mb-2">
                                                                    <span className="text-[11px] font-bold text-mq-text-tertiary uppercase tracking-wider">{key}</span>
                                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${val.score > 0.7 ? 'bg-mq-red/10 text-mq-red border border-mq-red/20' : 'bg-mq-teal/10 text-mq-teal border border-mq-teal/20'}`}>{val.value}</span>
                                                                </div>
                                                                <div className="w-full h-1.5 bg-mq-void rounded-full border border-mq-border/50 overflow-hidden">
                                                                    <div 
                                                                        className={`h-full transition-all duration-1000 ease-out ${val.score > 0.7 ? 'bg-mq-red shadow-glow-red-subtle' : 'bg-mq-teal shadow-glow-teal-subtle'}`}
                                                                        style={{ width: `${(val.score || 0) * 100}%` }}
                                                                    />
                                                                </div>
                                                                <p className="text-[10px] text-mq-text-tertiary mt-2 line-clamp-1 opacity-0 group-hover:opacity-100 transition-apple">{val.evidence}</p>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {state.activeTab === 'analysis' && (
                                    <div className="space-y-6">
                                         <div className="p-6 border border-mq-border rounded-2xl bg-mq-surface/30 min-h-[400px]">
                                            <div className="flex justify-between items-center mb-6">
                                                <h3 className="text-[11px] font-bold text-mq-text-tertiary uppercase tracking-widest">Global Property Matrix</h3>
                                                <div className="flex bg-mq-elevated p-1 rounded-lg border border-mq-border">
                                                    <button onClick={() => setAnalysisView('chart')} className={`px-3 py-1 text-[10px] font-bold uppercase rounded ${analysisView === 'chart' ? 'bg-mq-cyan text-mq-black' : 'text-mq-text-tertiary hover:text-mq-text'}`}>Bubble</button>
                                                    <button onClick={() => setAnalysisView('heatmap')} className={`px-3 py-1 text-[10px] font-bold uppercase rounded ${analysisView === 'heatmap' ? 'bg-mq-cyan text-mq-black' : 'text-mq-text-tertiary hover:text-mq-text'}`}>Heatmap</button>
                                                </div>
                                            </div>
                                            {analysisView === 'chart' ? (
                                                <CandidateComparisonChart 
                                                    molecules={state.resultData.molecules}
                                                    selectedMolecule={state.selectedMolecule}
                                                    onMoleculeClick={(m) => setState(s => ({ ...s, selectedMolecule: m }))}
                                                />
                                            ) : (
                                                <ADMETHeatmap molecules={state.resultData.molecules} />
                                            )}
                                        </div>
                                        <div className="space-y-2">
                                            {state.resultData.molecules.map((m, i) => (
                                                <div key={i} onClick={() => setState(s => ({ ...s, selectedMolecule: m }))} className={`p-4 rounded-xl border transition-apple cursor-pointer flex justify-between items-center group ${
                                                    state.selectedMolecule?.smiles === m.smiles ? 'bg-mq-cyan/10 border-mq-cyan/40 shadow-glow-cyan-subtle' : 'bg-mq-surface/20 border-mq-border hover:border-mq-cyan/30'
                                                }`}>
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-8 h-8 rounded-lg bg-mq-void/40 border border-mq-border flex items-center justify-center text-[10px] font-bold text-mq-text-tertiary group-hover:text-mq-cyan">#{i+1}</div>
                                                        <div>
                                                            <div className="text-[13px] font-bold text-mq-text">{m.name}</div>
                                                            <div className="text-[10px] text-mq-text-tertiary font-mono uppercase tracking-tighter">BE: {m.bindingEnergy?.toFixed(2)} | SA: {m.saScore?.toFixed(1)}</div>
                                                        </div>
                                                    </div>
                                                    {i === 0 && <span className="text-[9px] font-bold text-mq-teal uppercase tracking-widest px-2 py-0.5 rounded-full border border-mq-teal/30 bg-mq-teal/5">Lead</span>}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {state.activeTab === 'synthesis' && (
                                    <div className="space-y-6">
                                        <div className="p-8 border border-mq-border rounded-2xl bg-mq-surface/30 relative overflow-hidden group">
                                            <div className="absolute right-[-20px] top-[-20px] w-40 h-40 bg-mq-teal/5 blur-[60px] rounded-full group-hover:bg-mq-teal/10 transition-apple" />
                                            <h3 className="text-[11px] font-bold text-mq-teal uppercase tracking-widest mb-8 flex items-center gap-3">
                                                <FlaskConicalIcon className="w-5 h-5" /> Retrosynthetic Pathway Analysis
                                            </h3>
                                            <div className="space-y-10 relative">
                                                <div className="absolute left-[9px] top-4 bottom-4 w-px bg-mq-border border-dashed border-l opacity-50" />
                                                {state.resultData.retrosynthesisPlan.map((s, i) => (
                                                    <div key={i} className="relative pl-10 animate-fade-in-up" style={{ animationDelay: `${i * 0.15}s` }}>
                                                        <div className="absolute left-0 top-1 w-5 h-5 rounded-full bg-mq-black border border-mq-border flex items-center justify-center text-[10px] font-bold text-mq-teal shadow-glow-teal-subtle z-10 transition-apple group-hover:scale-110">{i+1}</div>
                                                        <p className="text-[14px] text-mq-text-secondary leading-relaxed font-sans">{s}</p>
                                                    </div>
                                                ))}
                                                {(!state.resultData.retrosynthesisPlan || state.resultData.retrosynthesisPlan.length === 0) && <p className="text-mq-text-tertiary">No synthesis plan available.</p>}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {state.activeTab === 'knowledge' && (
                                    <div className="h-full flex flex-col gap-6">
                                        <div className="flex-1 min-h-[500px] border border-mq-border rounded-2xl bg-mq-surface/30 overflow-hidden relative shadow-inner">
                                            <KnowledgeGraph data={state.resultData.knowledgeGraphUpdate} />
                                        </div>
                                        <div className="p-5 bg-mq-cyan/5 border border-mq-cyan/20 rounded-2xl flex gap-4 items-center">
                                            <NetworkIcon className="w-6 h-6 text-mq-cyan opacity-60" />
                                            <p className="text-[11px] text-mq-text-tertiary leading-relaxed italic uppercase font-bold tracking-wider">Semantic Research Map: Interconnecting biological targets, chemical space, and lead candidates through hierarchical clustering.</p>
                                        </div>
                                    </div>
                                )}

                                {state.activeTab === 'plan' && (
                                    <div className="space-y-4">
                                        <div className="p-8 border border-mq-border rounded-2xl bg-mq-surface/30">
                                            <h3 className="text-[11px] font-bold text-mq-text-tertiary uppercase tracking-[0.2em] mb-8">Experimental Verification Protocol</h3>
                                            <div className="space-y-4">
                                                {state.resultData.experimentalPlan?.map((s, i) => (
                                                    <div key={i} className="flex gap-4 p-5 bg-mq-void/60 rounded-2xl border border-mq-border group hover:bg-mq-surface/20 transition-apple border-l-mq-cyan/40 border-l-2">
                                                        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-mq-elevated border border-mq-border flex items-center justify-center text-xs font-bold text-mq-text-tertiary group-hover:text-mq-cyan group-hover:shadow-glow-cyan-subtle">{i+1}</div>
                                                        <p className="text-[14px] text-mq-text-secondary leading-relaxed self-center">{s}</p>
                                                    </div>
                                                ))}
                                                {(!state.resultData.experimentalPlan || state.resultData.experimentalPlan.length === 0) && <p className="text-mq-text-tertiary text-center py-4">No plan available.</p>}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {state.activeTab === 'literature' && (
                                    <div className="space-y-4">
                                        {state.resultData.literature?.map((ref, i) => (
                                            <a key={i} href={ref.url} target="_blank" rel="noopener noreferrer" className="block p-6 border border-mq-border rounded-2xl bg-mq-surface/30 hover:border-mq-cyan/40 transition-apple group hover:bg-mq-surface/40 hover:shadow-xl">
                                                <div className="flex justify-between items-start mb-3">
                                                    <h4 className="text-[15px] font-bold text-mq-text group-hover:text-mq-cyan transition-apple leading-tight">{ref.title}</h4>
                                                    <div className="p-2 rounded-lg bg-mq-elevated border border-mq-border text-mq-text-tertiary opacity-0 group-hover:opacity-100 transition-apple">
                                                        <Share2Icon className="w-4 h-4" />
                                                    </div>
                                                </div>
                                                <p className="text-[13px] text-mq-text-tertiary leading-relaxed mb-4 border-l-2 border-mq-void/50 pl-4">{ref.summary}</p>
                                                <div className="flex items-center gap-2 text-[10px] font-mono text-mq-cyan/60">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-mq-cyan opacity-40" />
                                                    <span className="truncate">{ref.url}</span>
                                                </div>
                                            </a>
                                        ))}
                                        {(!state.resultData.literature || state.resultData.literature.length === 0) && <p className="text-mq-text-tertiary text-center py-4">No literature found.</p>}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </aside>
            </div>
        </div>
    );
}
