/* Milimo Quantum — Artifact Panel (Enhanced)
 *
 * Features:
 * - Syntax-highlighted code display
 * - Copy-to-clipboard with feedback
 * - Download code as .py file
 * - Interactive results histogram
 * - Circuit text rendering
 */
import { useMemo, useState, useCallback } from 'react';
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

/* ── Syntax-highlighted Code View ─────────────────────── */
function CodeView({ content, language, title }: { content: string; language?: string; title?: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [content]);

    const handleDownload = useCallback(() => {
        const ext = language === 'python' ? '.py' : language === 'javascript' ? '.js' : '.txt';
        const filename = (title || 'artifact').replace(/[^a-zA-Z0-9 ]/g, '').replace(/\s+/g, '_').toLowerCase() + ext;
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }, [content, language, title]);

    // Basic syntax highlighting for Python
    const highlighted = useMemo(() => highlightPython(content), [content]);

    return (
        <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] text-mq-text-tertiary font-mono tracking-wider uppercase">
                    {language || 'python'}
                </span>
                <div className="flex items-center gap-2">
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
            <pre className="!bg-black/60 border border-mq-border rounded-2xl p-5 overflow-x-auto glow-inset">
                <code
                    className="text-[13px] leading-[1.8]"
                    dangerouslySetInnerHTML={{ __html: highlighted }}
                />
            </pre>
        </div>
    );
}

/* ── Syntax Highlighting Engine (Python) ─────────────── */
function highlightPython(code: string): string {
    // Escape HTML first
    let html = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Comments (# ...)
    html = html.replace(/(#[^\n]*)/g,
        '<span style="color:#6a9955;font-style:italic">$1</span>');

    // Multi-line strings ("""...""" or '''...''')
    html = html.replace(/("""[\s\S]*?"""|'''[\s\S]*?''')/g,
        '<span style="color:#ce9178">$1</span>');

    // Strings ("..." or '...')
    html = html.replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,
        '<span style="color:#ce9178">$1</span>');

    // Keywords
    const keywords = ['from', 'import', 'def', 'class', 'return', 'if', 'else', 'elif',
        'for', 'in', 'while', 'try', 'except', 'finally', 'with', 'as',
        'and', 'or', 'not', 'True', 'False', 'None', 'lambda', 'yield',
        'raise', 'pass', 'break', 'continue', 'assert', 'global', 'async', 'await'];
    const kwRegex = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
    html = html.replace(kwRegex,
        '<span style="color:#c586c0;font-weight:500">$1</span>');

    // Built-in functions
    const builtins = ['print', 'range', 'len', 'list', 'dict', 'int', 'float', 'str',
        'type', 'isinstance', 'enumerate', 'zip', 'map', 'filter', 'sum',
        'min', 'max', 'abs', 'round', 'sorted', 'set', 'tuple', 'bool'];
    const biRegex = new RegExp(`\\b(${builtins.join('|')})(?=\\()`, 'g');
    html = html.replace(biRegex,
        '<span style="color:#dcdcaa">$1</span>');

    // Numbers
    html = html.replace(/\b(\d+\.?\d*(?:e[+-]?\d+)?)\b/g,
        '<span style="color:#b5cea8">$1</span>');

    // Function definitions - def name(
    html = html.replace(/\b(def\s+)(\w+)/g,
        '$1<span style="color:#dcdcaa">$2</span>');

    return html;
}

/* ── Circuit View ─────────────────────────────────────── */
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
