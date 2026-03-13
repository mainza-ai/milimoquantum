import { useState, useRef, useEffect } from 'react';
import { fetchWithAuth } from '../../services/api';
import { extensionSessionStore } from '../../services/sessionStore';

interface DrugDiscoveryPanelProps {
    instanceId: string;
    isOpen: boolean;
    onClose: () => void;
    currentConversationId?: string;
    onLoadConversation?: (id: string) => void;
}

export function DrugDiscoveryPanel({ instanceId, isOpen, onClose, currentConversationId, onLoadConversation }: DrugDiscoveryPanelProps) {
    const [prompt, setPrompt] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [statusLogs, setStatusLogs] = useState<string[]>([]);
    const [finalResult, setFinalResult] = useState<any>(null);
    const [eventError, setEventError] = useState('');
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Persistence: Load on mount
    useEffect(() => {
        // 1. Try local session store first (ephemeral)
        const saved = extensionSessionStore.get<any>(instanceId);
        if (saved) {
            setPrompt(saved.prompt || '');
            setIsGenerating(saved.isGenerating || false);
            setStatusLogs(saved.statusLogs || []);
            setFinalResult(saved.finalResult || null);
            setEventError(saved.eventError || '');
        } else if (currentConversationId) {
            // 2. Fallback to backend (robust)
            const fetchLatest = async () => {
                try {
                    const res = await fetchWithAuth(`/api/mqdd/results/${currentConversationId}`, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        }
                    });
                    const data = await res.json();
                    if (data && !data.error) {
                        setFinalResult(data);
                        setStatusLogs(prev => [...prev, "[SYSTEM] Restored results from database."]);
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
            prompt,
            isGenerating,
            statusLogs,
            finalResult,
            eventError
        });
    }, [instanceId, prompt, isGenerating, statusLogs, finalResult, eventError]);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [statusLogs]);

    const handleRunWorkflow = async () => {
        if (!prompt.trim()) return;
        
        setIsGenerating(true);
        setStatusLogs([]);
        setFinalResult(null);
        setEventError('');

        try {
            const response = await fetchWithAuth('/api/mqdd/workflow', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({ 
                    prompt,
                    conversation_id: currentConversationId
                })
            });

            if (!response.body) {
                throw new Error("No readable stream available.");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
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
                            const dataRaw = eventMatch[2];

                            try {
                                const data = JSON.parse(dataRaw);
                                if (eventType === 'status') {
                                    setStatusLogs(prev => [...prev, `[${data.agent}] ${data.status}: ${data.message}`]);
                                    
                                    // If backend generated or matched a conversation_id, tell the parent
                                    if (data.conversation_id && data.conversation_id !== currentConversationId) {
                                        onLoadConversation?.(data.conversation_id);
                                    }
                                } else if (eventType === 'result') {
                                    setFinalResult(data);
                                    setIsGenerating(false);
                                } else if (eventType === 'error') {
                                    setEventError(data.message || 'Unknown error');
                                    setIsGenerating(false);
                                }
                            } catch (e) {
                                console.error("Failed to parse SSE data", dataRaw);
                            }
                        }
                    }
                }
            }
            setIsGenerating(false);

        } catch (error: any) {
            console.error("Workflow error:", error);
            setEventError(error.message || 'Failed to execute workflow.');
            setIsGenerating(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
            <div className="absolute inset-0" onClick={onClose} />
            <div className="relative w-full max-w-6xl h-[85vh] glass-strong rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-slide-up border-mq-border">
                {/* Header */}
                <div className="px-6 py-5 border-b border-mq-border flex items-center justify-between bg-mq-surface/50 backdrop-blur-md">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mq-cyan/20 to-mq-cyan/5 border border-mq-cyan/30 flex items-center justify-center text-xl shadow-[0_0_20px_rgba(62,207,239,0.1)]">
                            🧬
                        </div>
                        <div>
                            <h2 className="text-[17px] font-bold text-mq-text tracking-tight uppercase">Quantum Drug Discovery</h2>
                            <p className="text-[11px] text-mq-cyan/70 font-mono tracking-widest uppercase">Local Engine — Ready</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-9 h-9 rounded-xl hover:bg-mq-hover flex items-center justify-center text-mq-text-secondary hover:text-mq-text transition-apple"
                    >
                        ✕
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 p-8 flex flex-col overflow-hidden bg-mq-void/40">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="flex-1 relative group">
                            <input 
                                type="text" 
                                className="w-full bg-mq-surface/30 border border-mq-border rounded-xl px-5 py-3.5 text-[15px] text-mq-text focus:outline-none focus:border-mq-cyan focus:bg-mq-surface/50 transition-apple shadow-inner font-sans placeholder:text-mq-text-tertiary"
                                placeholder="Describe research target (e.g., 'Find an inhibitor for BRAF V600E')"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !isGenerating && handleRunWorkflow()}
                                disabled={isGenerating}
                            />
                            <div className="absolute inset-0 rounded-xl border border-mq-cyan/20 opacity-0 group-focus-within:opacity-100 transition-apple pointer-events-none blur-sm" />
                        </div>
                        <button 
                            className={`px-8 py-3.5 rounded-xl text-[15px] font-bold transition-apple tracking-tight ${
                                isGenerating 
                                ? 'bg-mq-hover text-mq-text-tertiary cursor-not-allowed border border-mq-border' 
                                : 'bg-gradient-to-br from-mq-cyan to-mq-teal text-mq-black hover:brightness-110 cursor-pointer shadow-[0_8px_20px_rgba(62,207,239,0.3)] active:scale-95'
                            }`}
                            onClick={handleRunWorkflow}
                            disabled={isGenerating || !prompt.trim()}
                        >
                            {isGenerating ? 'ANALYZING...' : 'RUN PIPELINE'}
                        </button>
                    </div>

                    {eventError && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-[13px]">
                            {eventError}
                        </div>
                    )}

                    <div className="flex flex-1 gap-8 min-h-0">
                        {/* Status logs */}
                        <div className="w-[32%] bg-[#12121e]/80 border border-mq-border rounded-2xl flex flex-col overflow-hidden shadow-inner backdrop-blur-sm">
                            <div className="px-5 py-4 border-b border-mq-border bg-mq-surface/40 flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-mq-cyan uppercase tracking-[0.15em]">System Output</h3>
                                <div className="flex gap-1.5 grayscale opacity-40">
                                    <div className="w-2 h-2 rounded-full bg-mq-cyan" />
                                    <div className="w-2 h-2 rounded-full bg-mq-cyan" />
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-5 space-y-2.5 font-mono text-[12px]">
                                {statusLogs.map((log, i) => {
                                    const isSearch = log.includes('[Search]');
                                    const isAnalysis = log.includes('[Analysis]');
                                    const isDocking = log.includes('[Docking]');
                                    return (
                                        <div key={i} className="text-mq-text-secondary leading-relaxed break-words animate-fade-in-up">
                                            <span className={`${
                                                isSearch ? 'text-mq-cyan' : 
                                                isAnalysis ? 'text-mq-green' : 
                                                isDocking ? 'text-mq-ice' : 'text-mq-text-tertiary'
                                            } font-bold mr-2 select-none`}>•</span>
                                            {log}
                                        </div>
                                    );
                                })}
                                {isGenerating && (
                                    <div className="text-mq-cyan animate-pulse flex items-center gap-1">
                                        <span className="opacity-50">•</span>
                                        <div className="w-1.5 h-4 bg-mq-cyan/60 rounded-sm" />
                                    </div>
                                )}
                                <div ref={logsEndRef} />
                            </div>
                        </div>

                        {/* Results */}
                        <div className="w-[68%] bg-[#12121e]/40 border border-mq-border rounded-2xl flex flex-col overflow-hidden shadow-2xl backdrop-blur-xl">
                            <div className="px-5 py-4 border-b border-mq-border bg-mq-surface/40">
                                <h3 className="text-[11px] font-bold text-mq-silver uppercase tracking-[0.15em]">Quantum Analysis Report</h3>
                            </div>
                            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                                {!finalResult && !isGenerating && statusLogs.length === 0 && (
                                    <div className="h-full flex flex-col items-center justify-center text-center animate-fade-in">
                                        <div className="w-20 h-20 rounded-full border border-mq-border bg-mq-surface/10 flex items-center justify-center text-3xl mb-6 shadow-glow-subtle animate-float">
                                            🔬
                                        </div>
                                        <h4 className="text-mq-text text-[18px] font-bold mb-3 tracking-tight">System Ready for Simulation</h4>
                                        <p className="text-[14px] text-mq-text-secondary max-w-sm leading-relaxed">
                                            Define your target protein or molecular structure above to initialize the quantum docking pipeline.
                                        </p>
                                    </div>
                                )}
                                {finalResult && (
                                    <div className="space-y-10 animate-fade-in-up">
                                        <div className="bg-mq-surface/20 border border-mq-border rounded-2xl p-6">
                                            <h4 className="text-mq-cyan font-bold mb-3 text-[14px] uppercase tracking-wider flex items-center gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-mq-cyan shadow-[0_0_8px_#3ecfef]" />
                                                Executive Summary
                                            </h4>
                                            <p className="text-mq-text-secondary text-[15px] leading-relaxed font-sans">{finalResult.summary}</p>
                                        </div>
 
                                        {finalResult.molecules?.length > 0 && (
                                            <div>
                                                <h4 className="text-mq-text font-bold mb-6 text-[16px] flex items-center gap-2">
                                                    Candidate Overview
                                                </h4>
                                                <div className="grid grid-cols-2 gap-6">
                                                    {finalResult.molecules.map((m: any, idx: number) => (
                                                        <div key={idx} className="bg-mq-surface/30 border border-mq-border rounded-2xl p-5 hover:border-mq-cyan/40 transition-apple hover:bg-mq-surface/50 group">
                                                            <div className="flex items-center justify-between mb-4">
                                                                <h5 className="text-mq-text font-bold text-[15px] group-hover:text-mq-cyan transition-apple">{m.name}</h5>
                                                                {idx === 0 && (
                                                                    <span className="bg-mq-cyan/20 text-mq-cyan text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(62,207,239,0.2)] animate-pulse">
                                                                        LEAD
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <div className="text-[12px] font-mono text-mq-cyan/80 break-all bg-mq-black/50 p-3 rounded-xl mb-4 border border-mq-border/50">
                                                                {m.smiles}
                                                            </div>
                                                            <div className="flex items-center justify-between text-[13px] py-1 border-b border-mq-border mb-1">
                                                                <span className="text-mq-text-tertiary">Binding Affinity</span>
                                                                <span className={`font-bold ${m.bindingEnergy < -10 ? 'text-mq-cyan' : 'text-mq-text'}`}>
                                                                    {m.bindingEnergy?.toFixed(2) || 'N/A'} kJ/mol
                                                                </span>
                                                            </div>
                                                            {m.admet && (
                                                                <div className="flex items-center justify-between text-[13px] pt-1">
                                                                    <span className="text-mq-text-tertiary">Toxicity Index</span>
                                                                    <span className={`font-bold ${m.admet.toxicity?.score > 0.5 ? 'text-mq-red' : 'text-mq-green'}`}>
                                                                        {m.admet.toxicity?.score?.toFixed(2) || 'N/A'}
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {finalResult.experimentalPlan?.length > 0 && (
                                            <div className="bg-mq-surface/10 border border-mq-border rounded-2xl p-6">
                                                <h4 className="text-mq-text font-bold mb-5 text-[15px]">Validation Workflow</h4>
                                                <div className="space-y-4">
                                                    {finalResult.experimentalPlan.map((step: string, idx: number) => (
                                                        <div key={idx} className="flex items-start gap-4">
                                                            <div className="w-6 h-6 rounded-lg bg-mq-cyan/10 border border-mq-cyan/30 flex items-center justify-center text-[11px] font-bold text-mq-cyan flex-shrink-0 mt-0.5">
                                                                {idx + 1}
                                                            </div>
                                                            <p className="text-mq-text-secondary text-[14px] leading-relaxed">{step}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        
                                        {finalResult.proactiveSuggestions?.length > 0 && (
                                            <div>
                                                <h4 className="text-mq-text-tertiary font-bold mb-4 text-[13px] uppercase tracking-widest">Injective Steps</h4>
                                                <div className="flex gap-3 flex-wrap">
                                                    {finalResult.proactiveSuggestions.map((sug: string, idx: number) => (
                                                        <div key={idx} className="bg-mq-elevated/40 hover:bg-mq-cyan/10 hover:border-mq-cyan/30 cursor-pointer transition-apple border border-mq-border rounded-xl px-5 py-2.5 text-[13px] text-mq-text-secondary hover:text-mq-cyan">
                                                            {sug}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
