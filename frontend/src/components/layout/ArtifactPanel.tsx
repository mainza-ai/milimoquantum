/* Milimo Quantum — Artifact Panel (Enhanced)
 *
 * Features:
 * - Monaco editor for code with edit/re-run
 * - Copy-to-clipboard with feedback
 * - Download code as .py file
 * - Interactive results histogram
 * - Circuit text rendering
 */
import { useMemo, useState, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { CircuitVisualizer } from '../quantum/CircuitVisualizer';
import type { Artifact } from '../../types';

interface ArtifactPanelProps {
    artifact: Artifact | null;
    onClose: () => void;
}

export function ArtifactPanel({ artifact, onClose }: ArtifactPanelProps) {
    if (!artifact) return null;

    return (
        <div className="w-[420px] shrink-0 border-l border-mq-border bg-mq-void
      flex flex-col animate-slide-in-right overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-mq-border">
                <div className="flex items-center gap-2.5 min-w-0">
                    <ArtifactTypeIcon type={artifact.type} />
                    <h3 className="text-[13px] font-semibold text-mq-text truncate tracking-tight">
                        {artifact.title}
                    </h3>
                </div>
                <button
                    onClick={onClose}
                    className="w-7 h-7 rounded-lg flex items-center justify-center
            text-mq-text-tertiary hover:text-mq-text text-xs
            hover:bg-mq-hover transition-all duration-200 cursor-pointer"
                >
                    ✕
                </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-auto p-5">
                {artifact.type === 'code' && <CodeView content={artifact.content} language={artifact.language} title={artifact.title} />}
                {artifact.type === 'circuit' && <CircuitView content={artifact.content} />}
                {artifact.type === 'results' && <ResultsView content={artifact.content} metadata={artifact.metadata} />}
            </div>
        </div>
    );
}

function ArtifactTypeIcon({ type }: { type: string }) {
    const icons: Record<string, string> = { code: '💻', circuit: '🔌', results: '📊', notebook: '📓', report: '📄' };
    return <span className="text-[15px] shrink-0">{icons[type] || '📄'}</span>;
}

/* ── Monaco Code View ─────────────────────────────────── */
function CodeView({ content, language, title }: { content: string; language?: string; title?: string }) {
    const [copied, setCopied] = useState(false);
    const [editable, setEditable] = useState(false);
    const [code, setCode] = useState(content);
    const [running, setRunning] = useState(false);
    const [runResult, setRunResult] = useState<string | null>(null);

    // Keep code in sync when artifact changes
    useMemo(() => setCode(content), [content]);

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [code]);

    const handleDownload = useCallback(() => {
        const ext = language === 'python' ? '.py' : language === 'javascript' ? '.js' : '.txt';
        const filename = (title || 'artifact').replace(/[^a-zA-Z0-9 ]/g, '').replace(/\s+/g, '_').toLowerCase() + ext;
        const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }, [code, language, title]);

    const handleRerun = useCallback(async () => {
        setRunning(true);
        setRunResult(null);
        try {
            const res = await fetch('/api/quantum/execute-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();
            if (data.success) {
                setRunResult(`✅ Executed in ${data.execution_time_ms}ms` +
                    (data.stdout ? `\n${data.stdout}` : ''));
            } else {
                setRunResult(`❌ ${data.error || 'Execution failed'}`);
            }
        } catch {
            setRunResult('❌ Connection failed');
        } finally {
            setRunning(false);
        }
    }, [code]);



    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] text-mq-text-tertiary font-mono tracking-wider uppercase">
                    {language || 'python'}
                </span>
                <div className="flex items-center gap-2">
                    {/* Re-run button */}
                    <button
                        onClick={handleRerun}
                        disabled={running}
                        className={`text-[11px] font-medium transition-all duration-200 cursor-pointer tracking-wide
              flex items-center gap-1 px-2 py-0.5 rounded-md
              ${running
                                ? 'text-yellow-400 bg-yellow-400/10'
                                : 'text-green-400/80 hover:text-green-400 hover:bg-green-400/10'
                            }`}
                        title="Re-run code in sandbox"
                    >
                        {running ? (
                            <><span className="animate-spin inline-block w-3 h-3 border border-yellow-400 border-t-transparent rounded-full" /> Running...</>
                        ) : (
                            <>▶ Re-run</>
                        )}
                    </button>
                    {/* Edit toggle */}
                    <button
                        onClick={() => setEditable(!editable)}
                        className={`text-[11px] font-medium transition-colors duration-200 cursor-pointer tracking-wide
              ${editable ? 'text-mq-cyan' : 'text-mq-text-tertiary hover:text-mq-cyan/70'}`}
                    >
                        {editable ? '🔒 Lock' : '✏️ Edit'}
                    </button>
                    <button
                        onClick={handleDownload}
                        className="text-[11px] text-mq-text-tertiary hover:text-mq-cyan font-medium
              transition-colors duration-200 cursor-pointer tracking-wide flex items-center gap-1"
                        title="Download file"
                    >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Download
                    </button>
                    <button
                        onClick={handleCopy}
                        className={`text-[11px] font-medium transition-all duration-300 cursor-pointer tracking-wide ${copied ? 'text-green-400' : 'text-mq-cyan/70 hover:text-mq-cyan'
                            }`}
                    >
                        {copied ? '✓ Copied!' : 'Copy'}
                    </button>
                </div>
            </div>

            {/* Editor */}
            <div className="rounded-2xl overflow-hidden border border-mq-border glow-inset">
                <Editor
                    height="350px"
                    language={language || 'python'}
                    theme="vs-dark"
                    value={code}
                    onChange={(v: string | undefined) => editable && setCode(v || '')}
                    options={{
                        readOnly: !editable,
                        minimap: { enabled: false },
                        fontSize: 13,
                        lineHeight: 1.8,
                        scrollBeyondLastLine: false,
                        padding: { top: 16, bottom: 16 },
                        automaticLayout: true,
                        wordWrap: 'on',
                        scrollbar: { verticalScrollbarSize: 6 },
                    }}
                />
            </div>

            {/* Run result */}
            {runResult && (
                <pre className="mt-3 text-[12px] leading-relaxed bg-black/40 border border-mq-border
          rounded-xl p-3 text-mq-text-secondary whitespace-pre-wrap animate-fade-in">
                    {runResult}
                </pre>
            )}
        </div>
    );
}


/* ── Circuit View ─────────────────────────────────────── */
function CircuitView({ content }: { content: string }) {
    return (
        <div className="animate-fade-in space-y-4">
            {/* Interactive SVG circuit */}
            <div className="bg-black/40 border border-mq-border rounded-2xl p-4 overflow-x-auto glow-inset">
                <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-3 font-medium">Interactive Circuit Diagram</p>
                <CircuitVisualizer code={content} />
            </div>

            {/* Raw circuit text */}
            <div className="bg-black/60 border border-mq-border rounded-2xl p-5 overflow-x-auto">
                <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-2 font-medium">Circuit Text</p>
                <pre className="!bg-transparent !border-none !p-0 text-mq-cyan font-mono text-[12px] leading-relaxed whitespace-pre">
                    {content}
                </pre>
            </div>
        </div>
    );
}

/* ── Results View with Interactive Histogram ──────────── */
function ResultsView({
    content,
    metadata,
}: {
    content: string;
    metadata?: Record<string, unknown>;
}) {
    const counts = useMemo(() => {
        try { return JSON.parse(content) as Record<string, number>; }
        catch { return {}; }
    }, [content]);

    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const maxCount = Math.max(...entries.map(([, v]) => v), 1);
    const totalShots = (metadata?.shots as number) || entries.reduce((s, [, v]) => s + v, 0) || 1024;
    const [hoveredState, setHoveredState] = useState<string | null>(null);

    return (
        <div className="animate-fade-in space-y-5">
            {/* Metrics */}
            {metadata && (
                <div className="grid grid-cols-2 gap-2.5">
                    {!!metadata.shots && <Metric label="Shots" value={String(metadata.shots)} />}
                    {!!metadata.execution_time_ms && <Metric label="Time" value={`${String(metadata.execution_time_ms)}ms`} />}
                    {!!metadata.num_qubits && <Metric label="Qubits" value={String(metadata.num_qubits)} />}
                    {!!metadata.depth && <Metric label="Depth" value={String(metadata.depth)} />}
                    {!!metadata.trainable_params && <Metric label="Parameters" value={String(metadata.trainable_params)} />}
                    {!!metadata.backend && <Metric label="Backend" value={String(metadata.backend).replace('aer_', '')} />}
                </div>
            )}

            {/* Histogram */}
            <div>
                <p className="text-[10px] text-mq-text-tertiary tracking-[0.14em] uppercase font-medium mb-3">
                    Measurement Distribution ({entries.length} states)
                </p>
                <div className="space-y-3">
                    {entries.slice(0, 16).map(([state, count]) => {
                        const pct = (count / maxCount) * 100;
                        const prob = ((count / totalShots) * 100).toFixed(1);
                        const isHovered = hoveredState === state;
                        return (
                            <div
                                key={state}
                                onMouseEnter={() => setHoveredState(state)}
                                onMouseLeave={() => setHoveredState(null)}
                                className="transition-all duration-200"
                                style={{ transform: isHovered ? 'scale(1.02)' : 'scale(1)' }}
                            >
                                <div className="flex items-center justify-between text-[12px] mb-1.5">
                                    <span className="font-mono text-mq-cyan font-medium tracking-wide">|{state}⟩</span>
                                    <span className="text-mq-text-secondary tabular-nums">{count} <span className="text-mq-text-tertiary">({prob}%)</span></span>
                                </div>
                                <div className="h-8 rounded-xl overflow-hidden bg-black/40 border border-mq-border">
                                    <div
                                        className="h-full rounded-xl flex items-center px-3
                      transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
                                        style={{
                                            width: `${pct}%`,
                                            background: isHovered
                                                ? 'linear-gradient(90deg, #3ecfef, #5be0ff)'
                                                : 'linear-gradient(90deg, #2ba8c4, #3ecfef)',
                                            boxShadow: isHovered
                                                ? '0 0 20px rgba(62,207,239,0.4)'
                                                : '0 0 12px rgba(62,207,239,0.2)',
                                        }}
                                    >
                                        {pct > 20 && (
                                            <span className="text-[10px] font-bold text-mq-black/80">{prob}%</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                    {entries.length > 16 && (
                        <p className="text-[11px] text-mq-text-tertiary text-center pt-2">
                            + {entries.length - 16} more states
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div className="glass rounded-xl p-3.5">
            <div className="text-[10px] text-mq-text-tertiary uppercase tracking-[0.12em] font-medium">{label}</div>
            <div className="text-lg font-semibold text-mq-text mt-1 tracking-tight">{value}</div>
        </div>
    );
}
