import { useMemo, useState } from 'react';

export function ResultsView({
    content,
    metadata,
}: {
    content: string;
    metadata?: Record<string, any>;
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
