import { useState, useRef, useEffect } from 'react';
import { fetchWithAuth } from '../../services/api';
import { useProject } from '../../contexts/ProjectContext';
import { extensionSessionStore } from '../../services/sessionStore';
import ReactMarkdown from 'react-markdown';

interface AutoresearchPanelProps {
    instanceId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function AutoresearchPanel({ instanceId, isOpen, onClose }: AutoresearchPanelProps) {
    const { activeProjectId } = useProject();
    const [isRunning, setIsRunning] = useState(false);
    const [researchTarget, setResearchTarget] = useState(activeProjectId || '');
    const [mode, setMode] = useState<'manual' | 'autonomous'>('manual');
    const [results, setResults] = useState<{columns: string[], rows: string[][]}>({columns: [], rows: []});
    const [logs, setLogs] = useState<string[]>([]);
    const [metrics, setMetrics] = useState<{name: string, value: string}[]>([]);
    const [status, setStatus] = useState('Idle');
    const [analysis, setAnalysis] = useState<string>('');
    const [showAnalysis, setShowAnalysis] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);

    const fetchResults = async () => {
        try {
            const res = await fetchWithAuth('/api/autoresearch/results');
            const data = await res.json();
            if (data.rows) setResults(data);
        } catch (e) {
            console.error("Failed to fetch results", e);
        }
    };

    // Persistence: Load on mount
    useEffect(() => {
        const saved = extensionSessionStore.get<any>(instanceId);
        if (saved) {
            setIsRunning(saved.isRunning || false);
            setResearchTarget(saved.researchTarget || '');
            setMode(saved.mode || 'manual');
            setLogs(saved.logs || []);
            setMetrics(saved.metrics || []);
            setStatus(saved.status || 'Idle');
        }
        fetchResults();
    }, [instanceId]);

    // Persistence: Save on change
    useEffect(() => {
        extensionSessionStore.set(instanceId, {
            isRunning,
            researchTarget,
            mode,
            logs,
            metrics,
            status
        });
    }, [instanceId, isRunning, researchTarget, mode, logs, metrics, status]);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    const handleExport = async () => {
        setLogs(prev => [...prev, 'Attempting to export dataset...']);
        try {
            const res = await fetchWithAuth(`/api/autoresearch/export${researchTarget ? `?project=${researchTarget}` : ''}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            if (res.ok) {
                setLogs(prev => [...prev, `Dataset exported to local Parquet cache.`]);
            } else {
                setLogs(prev => [...prev, `Export failed: ${res.statusText}`]);
            }
        } catch (e: any) {
            setLogs(prev => [...prev, `Export error: ${e.message}`]);
        }
    };

    const handleAnalyze = async () => {
        setLogs(prev => [...prev, 'Analyzing results with specialized agent...']);
        try {
            const res = await fetchWithAuth('/api/autoresearch/analyze', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            const data = await res.json();
            if (data.summary) {
                setAnalysis(data.summary);
                setShowAnalysis(true);
                setLogs(prev => [...prev, `Analysis complete.`]);
            }
        } catch (e: any) {
            setLogs(prev => [...prev, `Analysis error: ${e.message}`]);
        }
    };

    const handleDataPrep = async () => {
        setIsRunning(true);
        setLogs([]);
        setStatus('Preparing Data...');
        try {
            const response = await fetchWithAuth('/api/autoresearch/prepare', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            if (!response.body) return;
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                const events = chunk.split('\n\n');
                for (const event of events) {
                    if (event.startsWith('event: log')) {
                        const data = JSON.parse(event.split('data: ')[1]);
                        setLogs(prev => [...prev, data.text]);
                    } else if (event.startsWith('event: status')) {
                        const data = JSON.parse(event.split('data: ')[1]);
                        setStatus(data.message);
                        if (data.status === 'completed') setIsRunning(false);
                    }
                }
            }
        } catch (e: any) {
            setStatus('Prepare Error: ' + e.message);
            setIsRunning(false);
        }
    };

    const handleStartLoop = async () => {
        setIsRunning(true);
        setLogs([]);
        setMetrics([]);
        setStatus(mode === 'autonomous' ? 'Autonomous Mode Starting...' : 'Starting Experiment...');

        try {
            const response = await fetchWithAuth('/api/autoresearch/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({ target: researchTarget, mode: mode })
            });

            if (!response.body) throw new Error("No readable stream");

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) {
                    fetchResults();
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const part of parts) {
                    if (part.startsWith('event: ')) {
                        const eventMatch = part.match(/event: (.*)\ndata: (.*)/s);
                        if (eventMatch) {
                            const eventType = eventMatch[1];
                            const data = JSON.parse(eventMatch[2]);

                            if (eventType === 'log') {
                                setLogs(prev => [...prev, data.text]);
                            } else if (eventType === 'metric') {
                                setMetrics(prev => {
                                    const existing = prev.findIndex(m => m.name === data.name);
                                    if (existing >= 0) {
                                        const next = [...prev];
                                        next[existing] = data;
                                        return next;
                                    }
                                    return [...prev, data];
                                });
                            } else if (eventType === 'status') {
                                setStatus(data.message);
                                if (data.status === 'completed') setIsRunning(false);
                            } else if (eventType === 'error') {
                                setStatus('Error: ' + data.message);
                                setIsRunning(false);
                            }
                        }
                    }
                }
            }
        } catch (error: any) {
            setStatus('Failed: ' + error.message);
            setIsRunning(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
            <div className="absolute inset-0" onClick={onClose} />
            <div className="relative w-full max-w-6xl h-[85vh] glass-strong rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-slide-up border-mq-border">
                {/* Header */}
                <div className="px-6 py-5 border-b border-mq-border flex items-center justify-between bg-mq-surface/50 backdrop-blur-md">
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl transition-all duration-700 ${isRunning ? 'bg-mq-cyan/20 shadow-[0_0_20px_rgba(62,207,239,0.3)] animate-pulse' : 'bg-mq-surface/20 border border-mq-border'}`}>
                            {isRunning ? '🚀' : '🔭'}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h2 className="text-[17px] font-bold text-mq-text tracking-tight uppercase">Autoresearch-MLX</h2>
                                {isRunning && (
                                    <span className="flex h-2 w-2 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mq-cyan opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-mq-cyan"></span>
                                    </span>
                                )}
                            </div>
                            <p className="text-[11px] text-mq-cyan/70 font-mono tracking-widest uppercase">{status}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="hidden md:flex items-center gap-6 pr-6 border-r border-mq-border">
                            {metrics.map((m, i) => (
                                <div key={i} className="flex flex-col items-end">
                                    <span className="text-[9px] text-mq-text-tertiary uppercase tracking-widest font-bold">{m.name}</span>
                                    <span className="text-[16px] font-mono text-mq-cyan font-bold">{m.value}</span>
                                </div>
                            ))}
                        </div>
                        <button
                            onClick={onClose}
                            className="w-9 h-9 rounded-xl hover:bg-mq-hover flex items-center justify-center text-mq-text-secondary hover:text-mq-text transition-apple"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 p-8 flex flex-col gap-8 overflow-hidden bg-mq-void/40">
                    {/* Controls & Focus */}
                    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] items-end gap-6">
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center justify-between gap-4">
                                <div className="flex-1">
                                    <h3 className="text-mq-text text-[15px] font-bold tracking-tight mb-1">Research Objective</h3>
                                    <p className="text-mq-text-tertiary text-[12px]">Define the training target and focus area for the MLX autonomous agent.</p>
                                </div>
                                <div className="flex bg-mq-surface/30 rounded-xl p-1 border border-mq-border">
                                    <button
                                        onClick={() => setMode('manual')}
                                        className={`px-5 py-1.5 rounded-lg text-[10px] font-bold transition-apple tracking-widest uppercase ${mode === 'manual' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                    >
                                        Manual
                                    </button>
                                    <button
                                        onClick={() => setMode('autonomous')}
                                        className={`px-5 py-1.5 rounded-lg text-[10px] font-bold transition-apple tracking-widest uppercase ${mode === 'autonomous' ? 'bg-mq-cyan text-mq-black shadow-glow-cyan' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                    >
                                        Auto
                                    </button>
                                </div>
                            </div>
                            
                            <div className="relative group">
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-mq-cyan/40 text-[10px] font-bold tracking-tighter uppercase select-none">Target //</span>
                                <input 
                                    type="text"
                                    className="w-full bg-mq-surface/20 border border-mq-border rounded-xl pl-20 pr-4 py-3.5 text-[14px] text-mq-cyan focus:outline-none focus:border-mq-cyan/50 focus:bg-mq-surface/40 transition-apple font-mono shadow-inner"
                                    placeholder={mode === 'autonomous' ? "Search focus (e.g. attention optimization)" : "Project name or tag"}
                                    value={researchTarget}
                                    onChange={(e) => setResearchTarget(e.target.value)}
                                    disabled={isRunning}
                                />
                                <div className="absolute inset-0 rounded-xl border border-mq-cyan/10 opacity-0 group-focus-within:opacity-100 transition-apple pointer-events-none blur-sm" />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={handleDataPrep}
                                disabled={isRunning}
                                className="px-5 py-3 rounded-xl bg-mq-elevated/40 border border-mq-border text-[13px] font-bold text-mq-text-secondary hover:text-mq-text hover:bg-mq-elevated/60 transition-apple flex items-center gap-2"
                            >
                                <span className="text-[14px]">📊</span> Data Prep
                            </button>
                            <button
                                onClick={handleStartLoop}
                                disabled={isRunning}
                                className={`px-8 py-3 rounded-xl text-[14px] font-bold transition-all transform active:scale-95 flex items-center gap-2 ${
                                    isRunning
                                    ? 'bg-mq-hover text-mq-text-tertiary cursor-not-allowed border border-mq-border'
                                    : 'bg-gradient-to-br from-mq-cyan to-mq-teal text-mq-black hover:brightness-110 shadow-[0_8px_20px_rgba(62,207,239,0.3)]'
                                }`}
                            >
                                {isRunning ? (
                                    <>
                                        <div className="w-3 h-3 border-2 border-mq-text-tertiary border-t-transparent rounded-full animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        🚀 {mode === 'autonomous' ? 'Initialize Loop' : 'Run Experiment'}
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Operational View */}
                    <div className="flex-1 flex flex-col md:flex-row gap-8 overflow-hidden min-h-0">
                        {/* Console Output */}
                        <div className="flex-1 bg-[#0a0a0f]/80 border border-mq-border rounded-2xl flex flex-col overflow-hidden shadow-inner backdrop-blur-sm">
                            <div className="px-5 py-3 border-b border-mq-border bg-mq-surface/40 flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-mq-cyan uppercase tracking-[0.2em] select-none">MLX-Runtime Logs</h3>
                                <div className="flex gap-4">
                                    <button onClick={handleExport} className="text-[9px] font-bold text-mq-text-tertiary hover:text-mq-cyan transition-apple flex items-center gap-1.5 uppercase">
                                        <span>📥</span> Export Parquet
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-6 font-mono text-[12px] selection:bg-mq-cyan selection:text-mq-black custom-scrollbar">
                                {logs.length === 0 && !isRunning && (
                                    <div className="h-full flex flex-col items-center justify-center opacity-20 select-none">
                                        <div className="w-16 h-16 border border-mq-border rounded-3xl mb-4 flex items-center justify-center text-3xl animate-float">
                                            ⌨️
                                        </div>
                                        <p className="text-[10px] font-bold uppercase tracking-[0.3em]">Console Pending — Logic Awaiting Input</p>
                                    </div>
                                )}
                                {logs.map((log, i) => (
                                    <div key={i} className="mb-1 animate-fade-in-up group flex items-start gap-4">
                                        <span className="text-mq-text-tertiary/30 select-none font-bold min-w-[28px] text-right">{i+1}</span>
                                        <span className="text-mq-text-secondary group-hover:text-mq-text transition-colors break-words">{log}</span>
                                    </div>
                                ))}
                                {isRunning && (
                                    <div className="flex items-start gap-4 mt-2 animate-pulse">
                                        <span className="text-mq-cyan/30 select-none font-bold min-w-[28px] text-right">{logs.length + 1}</span>
                                        <div className="w-2 h-4 bg-mq-cyan/60 rounded-sm" />
                                    </div>
                                )}
                                <div ref={logsEndRef} />
                            </div>
                        </div>

                        {/* Results / Analysis Panel */}
                        <div className="w-full md:w-[420px] bg-[#12121e]/40 border border-mq-border rounded-2xl flex flex-col overflow-hidden shadow-2xl backdrop-blur-xl">
                            <div className="px-5 py-4 border-b border-mq-border bg-mq-surface/40 flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-mq-silver uppercase tracking-[0.15em]">{showAnalysis ? 'Scientific Summary' : 'Research Records'}</h3>
                                <div className="flex bg-mq-surface/30 rounded-lg p-0.5 border border-mq-border">
                                    <button 
                                        onClick={() => setShowAnalysis(false)}
                                        className={`px-3 py-1 rounded-md text-[9px] font-bold transition-all uppercase ${!showAnalysis ? 'bg-mq-elevated text-mq-cyan' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                    >
                                        Table
                                    </button>
                                    <button 
                                        onClick={() => {
                                            if (!analysis) handleAnalyze();
                                            else setShowAnalysis(true);
                                        }}
                                        className={`px-3 py-1 rounded-md text-[9px] font-bold transition-all uppercase ${showAnalysis ? 'bg-mq-elevated text-mq-cyan' : 'text-mq-text-tertiary hover:text-mq-text'}`}
                                    >
                                        Analysis
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar">
                                {showAnalysis ? (
                                    <div className="p-6 markdown-content">
                                        <ReactMarkdown>{analysis || "Initializing research analysis engine..."}</ReactMarkdown>
                                        {!analysis && (
                                            <div className="flex flex-col items-center justify-center py-12 text-mq-text-tertiary gap-4">
                                                <div className="w-8 h-8 border-2 border-mq-cyan/30 border-t-mq-cyan rounded-full animate-spin" />
                                                <p className="text-[10px] uppercase tracking-widest">Aggregating Experiment Data</p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="min-w-full">
                                        <table className="w-full text-left border-collapse">
                                            <thead className="sticky top-0 bg-mq-surface/90 backdrop-blur-md z-10">
                                                <tr className="border-b border-white/[0.05]">
                                                    <th className="px-5 py-3 text-[9px] text-mq-text-tertiary uppercase font-bold tracking-wider">Commit</th>
                                                    <th className="px-5 py-3 text-[9px] text-mq-text-tertiary uppercase font-bold tracking-wider text-right">Metric</th>
                                                    <th className="px-5 py-3 text-[9px] text-mq-text-tertiary uppercase font-bold tracking-wider text-center">Status</th>
                                                </tr>
                                            </thead>
                                            <tbody className="text-[12px] font-mono">
                                                {results.rows.length === 0 ? (
                                                    <tr>
                                                        <td colSpan={3} className="px-5 py-20 text-center text-mq-text-tertiary italic">
                                                            <div className="text-2xl mb-3 opacity-20">📊</div>
                                                            No records found
                                                        </td>
                                                    </tr>
                                                ) : (
                                                    [...results.rows].reverse().map((row, i) => (
                                                        <tr key={i} className="border-b border-white/[0.02] hover:bg-mq-surface/30 transition-apple group">
                                                            <td className="px-5 py-4 text-mq-cyan/70 group-hover:text-mq-cyan transition-apple">{row[0]}</td>
                                                            <td className="px-5 py-4 text-right text-mq-text font-bold">{row[1]}</td>
                                                            <td className="px-5 py-4 text-center">
                                                                <span className={`px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-tighter ${
                                                                    row[3] === 'keep' ? 'bg-mq-green/10 text-mq-green border border-mq-green/20 shadow-[0_0_10px_rgba(92,184,160,0.1)]' : 
                                                                    row[3] === 'discard' ? 'bg-mq-red/10 text-mq-red border border-mq-red/20' : 
                                                                    'bg-mq-amber/10 text-mq-amber border border-mq-amber/20'
                                                                }`}>
                                                                    {row[3]}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
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
