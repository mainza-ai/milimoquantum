import { useMemo } from 'react';

export function DatasetView({ content, metadata }: { content: string; metadata?: Record<string, any> }) {
    // Attempt to parse dataset - could be CSV strings, JSON arrays, etc.
    const dataPreview = useMemo(() => {
        try {
            // First try JSON layout
            const parsed = JSON.parse(content);
            if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object') {
                return {
                    format: 'json',
                    headers: Object.keys(parsed[0]),
                    rows: parsed.slice(0, 10), // Preview first 10
                    totalRows: parsed.length
                };
            }
            return { format: 'raw', content: JSON.stringify(parsed, null, 2) };
        } catch {
            // Fallback to text/csv lines
            const lines = content.trim().split('\n');
            if (lines.length > 1 && lines[0].includes(',')) {
                return {
                    format: 'csv',
                    headers: lines[0].split(','),
                    rows: lines.slice(1, 11).map(line => line.split(',')), // Preview first 10
                    totalRows: lines.length - 1
                };
            }
            return { format: 'raw', content };
        }
    }, [content]);

    return (
        <div className="animate-fade-in space-y-4">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] text-mq-text-tertiary uppercase tracking-wider font-medium">
                    Dataset Preview
                </span>
                {dataPreview.totalRows && (
                    <span className="text-[11px] text-mq-cyan/80 bg-mq-cyan/10 px-2 py-0.5 rounded-full">
                        {dataPreview.totalRows} rows
                    </span>
                )}
            </div>

            <div className="bg-black/40 border border-mq-border rounded-xl overflow-hidden overflow-x-auto glow-inset">
                {dataPreview.format === 'raw' ? (
                    <pre className="p-4 text-[12px] text-mq-text-secondary font-mono whitespace-pre-wrap">
                        {dataPreview.content}
                    </pre>
                ) : (
                    <table className="w-full text-left border-collapse text-[12px]">
                        <thead>
                            <tr className="bg-black/60 border-b border-mq-border">
                                {dataPreview.headers?.map((header, i) => (
                                    <th key={i} className="px-4 py-2 font-medium text-mq-text-secondary whitespace-nowrap">
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-mq-border/50">
                            {dataPreview.rows?.map((row, i) => (
                                <tr key={i} className="hover:bg-mq-hover/50 transition-colors">
                                    {(dataPreview.format === 'csv' ? (row as string[]) : Object.values(row as Record<string, any>)).map((cell, j) => (
                                        <td key={j} className="px-4 py-2 text-mq-text-tertiary whitespace-nowrap font-mono">
                                            {String(cell)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {(dataPreview.format === 'json' || dataPreview.format === 'csv') && dataPreview.totalRows! > 10 && (
                <div className="text-center mt-2 text-[11px] text-mq-text-tertiary">
                    Showing 10 of {dataPreview.totalRows} rows.
                </div>
            )}

            {metadata?.description && (
                <p className="text-sm text-mq-text-secondary mt-4">
                    {metadata.description}
                </p>
            )}
        </div>
    );
}
