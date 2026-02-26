import { useState, useCallback, useMemo } from 'react';
import Editor from '@monaco-editor/react';

export function CodeView({ content, language, title }: { content: string; language?: string; title?: string }) {
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
            // 1. Submit job to Celery task queue via sandbox
            const res = await fetch('/api/jobs/execute-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();

            if (!data.job_id) {
                setRunResult(`❌ ${data.error || data.detail || 'Execution failed to queue'}`);
                setRunning(false);
                return;
            }

            const jobId = data.job_id;
            setRunResult('⏳ Queued for execution...');

            // 2. Poll for Status
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/jobs/${jobId}/status`);
                    const statusData = await statusRes.json();

                    if (statusData.status === 'SUCCESS') {
                        clearInterval(pollInterval);
                        setRunning(false);
                        const result = statusData.result;
                        if (result?.error) {
                            setRunResult(`❌ ${result.error}`);
                        } else {
                            setRunResult(`✅ Executed in ${result?.execution_time_ms || 0}ms` +
                                (result?.stdout ? `\n${result.stdout}` : '') +
                                (result?.artifacts?.length ? `\n\n⚡ Generated ${result.artifacts.length} new artifacts (check chat history for details).` : ''));
                        }
                    } else if (statusData.status === 'FAILURE') {
                        clearInterval(pollInterval);
                        setRunning(false);
                        setRunResult(`❌ ${statusData.error || 'Execution failed'}`);
                    } else if (statusData.status === 'REVOKED') {
                        clearInterval(pollInterval);
                        setRunning(false);
                        setRunResult('⏹ Cancelled');
                    } else {
                        // Update intermediate status
                        setRunResult(`⏳ ${statusData.message || statusData.status}`);
                    }
                } catch (e) {
                    clearInterval(pollInterval);
                    setRunning(false);
                    setRunResult('❌ Polling failed');
                }
            }, 1000); // poll every 1s

        } catch {
            setRunResult('❌ Connection failed');
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
