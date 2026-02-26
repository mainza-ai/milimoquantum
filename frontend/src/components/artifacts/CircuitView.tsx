import { CircuitVisualizer } from '../quantum/CircuitVisualizer';

export function CircuitView({ content, metadata }: { content: string; metadata?: Record<string, any> }) {
    return (
        <div className="animate-fade-in space-y-4">
            {/* Interactive SVG circuit */}
            <div className="bg-black/40 border border-mq-border rounded-2xl p-4 overflow-x-auto glow-inset">
                <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-3 font-medium">Interactive Circuit Diagram</p>
                <CircuitVisualizer code={content} />
            </div>

            {/* Raw circuit text */}
            {Boolean(metadata?.ascii_diagram) && (
                <div className="bg-black/60 border border-mq-border rounded-2xl p-5 overflow-x-auto">
                    <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-2 font-medium">Circuit Text</p>
                    <pre className="!bg-transparent !border-none !p-0 text-mq-cyan font-mono text-[12px] leading-relaxed whitespace-pre">
                        {String(metadata?.ascii_diagram)}
                    </pre>
                </div>
            )}
        </div>
    );
}
