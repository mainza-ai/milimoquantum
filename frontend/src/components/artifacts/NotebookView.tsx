import ReactMarkdown from 'react-markdown';

export function NotebookView({ content, metadata }: { content: string; metadata?: Record<string, any> }) {
    // Basic rendering of Jupyter Notebook content or executed cells
    return (
        <div className="animate-fade-in space-y-4">
            <div className="bg-black/20 border border-mq-border rounded-xl p-5 overflow-auto">
                <div className="prose prose-invert prose-sm max-w-none prose-headings:text-mq-text prose-a:text-mq-cyan prose-code:text-mq-cyan prose-pre:bg-black/50 prose-pre:border prose-pre:border-mq-border prose-strong:text-mq-text">
                    {/* Often notebook content returned by the backend as an artifact is a markdown export or JSON summary */}
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>
            </div>

            {metadata && (
                <div className="mt-4 border-t border-mq-border pt-4">
                    <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-2 font-medium">Execution Metadata</p>
                    <div className="grid grid-cols-2 gap-2">
                        {metadata.kernel && (
                            <div className="glass rounded-xl p-3">
                                <div className="text-[10px] text-mq-text-tertiary uppercase tracking-[0.12em] font-medium">Kernel</div>
                                <div className="text-sm font-semibold text-mq-text mt-1">{metadata.kernel}</div>
                            </div>
                        )}
                        {metadata.execution_time && (
                            <div className="glass rounded-xl p-3">
                                <div className="text-[10px] text-mq-text-tertiary uppercase tracking-[0.12em] font-medium">Execution Time</div>
                                <div className="text-sm font-semibold text-mq-text mt-1">{metadata.execution_time}</div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
