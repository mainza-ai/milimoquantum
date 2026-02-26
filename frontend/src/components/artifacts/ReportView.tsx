import ReactMarkdown from 'react-markdown';

export function ReportView({ content, metadata }: { content: string; metadata?: Record<string, any> }) {
    return (
        <div className="animate-fade-in space-y-4">
            <div className="bg-black/20 border border-mq-border rounded-xl p-5 overflow-auto markdown-body">
                {/* Custom styling for markdown content is assumed to be handled globally by markdown-body class, or you can add specific Tailwind classes below */}
                <div className="prose prose-invert prose-sm max-w-none prose-headings:text-mq-text prose-a:text-mq-cyan prose-code:text-mq-cyan prose-pre:bg-black/50 prose-pre:border prose-pre:border-mq-border prose-strong:text-mq-cyan">
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>
            </div>

            {metadata && Object.keys(metadata).length > 0 && (
                <div className="mt-4 border-t border-mq-border pt-4">
                    <p className="text-[10px] text-mq-text-tertiary uppercase tracking-wider mb-2 font-medium">Report Metadata</p>
                    <pre className="text-[11px] font-mono text-mq-text-secondary bg-black/40 p-3 rounded-lg border border-mq-border">
                        {JSON.stringify(metadata, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
