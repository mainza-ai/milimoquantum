/* Milimo Quantum — Artifact Panel */
import { useMemo } from 'react';
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
                {artifact.type === 'code' && <CodeView content={artifact.content} language={artifact.language} />}
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

function CodeView({ content, language }: { content: string; language?: string }) {
    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] text-mq-text-tertiary font-mono tracking-wider uppercase">
                    {language || 'python'}
                </span>
                <button
                    onClick={() => navigator.clipboard.writeText(content)}
                    className="text-[11px] text-mq-cyan/70 hover:text-mq-cyan font-medium
            transition-colors duration-200 cursor-pointer tracking-wide"
                >
                    Copy
                </button>
            </div>
            <pre className="!bg-black/60 border border-mq-border rounded-2xl p-5 overflow-x-auto glow-inset">
                <code className="text-[13px] leading-[1.8] text-mq-silver">{content}</code>
            </pre>
        </div>
    );
}

function CircuitView({ content }: { content: string }) {
    return (
        <div className="animate-fade-in">
            <div className="bg-black/60 border border-mq-border rounded-2xl p-5 overflow-x-auto glow-inset">
                <pre className="!bg-transparent !border-none !p-0 text-mq-cyan font-mono text-[12px] leading-relaxed whitespace-pre">
                    {content}
                </pre>
            </div>
        </div>
    );
}

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
    const totalShots = (metadata?.shots as number) || 1024;

    return (
        <div className="animate-fade-in space-y-5">
            {/* Metrics */}
            {metadata && (
                <div className="grid grid-cols-2 gap-2.5">
                    {metadata.shots && <Metric label="Shots" value={String(metadata.shots)} />}
                    {metadata.execution_time_ms && <Metric label="Time" value={`${String(metadata.execution_time_ms)}ms`} />}
                    {metadata.num_qubits && <Metric label="Qubits" value={String(metadata.num_qubits)} />}
                    {metadata.depth && <Metric label="Depth" value={String(metadata.depth)} />}
                </div>
            )}

            {/* Histogram */}
            <div>
                <p className="text-[10px] text-mq-text-tertiary tracking-[0.14em] uppercase font-medium mb-3">
                    Measurement Distribution
                </p>
                <div className="space-y-3">
                    {entries.map(([state, count]) => {
                        const pct = (count / maxCount) * 100;
                        const prob = ((count / totalShots) * 100).toFixed(1);
                        return (
                            <div key={state}>
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
                                            background: 'linear-gradient(90deg, #2ba8c4, #3ecfef)',
                                            boxShadow: '0 0 12px rgba(62,207,239,0.2)',
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
