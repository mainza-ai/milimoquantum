/* Milimo Quantum — Message Bubble */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage, Artifact } from '../../types';
import { AGENTS } from '../../types';

interface MessageBubbleProps {
    message: ChatMessage;
    onArtifactClick?: (artifact: Artifact) => void;
}

export function MessageBubble({ message, onArtifactClick }: MessageBubbleProps) {
    const isUser = message.role === 'user';
    const agent = AGENTS.find((a) => a.type === message.agent);

    return (
        <div className={`flex gap-3.5 animate-fade-in-up ${isUser ? 'justify-end' : ''}`}>
            {/* Agent avatar */}
            {!isUser && (
                <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center text-[14px] shrink-0 mt-0.5
            border border-mq-border transition-all duration-200"
                    style={{
                        background: `linear-gradient(135deg, ${agent?.color || '#3ecfef'}08, ${agent?.color || '#3ecfef'}15)`,
                        color: agent?.color || '#3ecfef',
                    }}
                >
                    {agent?.icon || '⚛'}
                </div>
            )}

            {/* Content */}
            <div className={`${isUser ? 'max-w-[75%]' : 'flex-1'}`}>
                {/* User bubble */}
                {isUser ? (
                    <div className="glass rounded-2xl rounded-tr-lg px-4 py-3">
                        <p className="text-[14px] text-mq-text leading-relaxed">{message.content}</p>
                    </div>
                ) : (
                    <>
                        {/* Agent label */}
                        {agent && (
                            <p className="text-[11px] font-medium mb-1.5 tracking-wide"
                                style={{ color: agent.color }}>
                                {agent.name}
                            </p>
                        )}

                        {/* Response */}
                        <div className="text-[14px] leading-relaxed markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    code({ className, children, ...props }) {
                                        const isInline = !className;
                                        if (isInline) {
                                            return (
                                                <code className="bg-mq-cyan/8 border border-mq-cyan/12 px-1.5 py-0.5 rounded-md text-mq-cyan text-[13px]" {...props}>
                                                    {children}
                                                </code>
                                            );
                                        }
                                        return (
                                            <pre className="!bg-black/50 border border-mq-border rounded-xl p-5 my-4 overflow-x-auto glow-inset">
                                                <code className={`${className} text-[13px] leading-relaxed`} {...props}>
                                                    {children}
                                                </code>
                                            </pre>
                                        );
                                    },
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                            {message.isStreaming && (
                                <span className="inline-flex ml-0.5 align-middle">
                                    <span className="w-[2px] h-[18px] bg-mq-cyan rounded-full"
                                        style={{ animation: 'typing-cursor 1s ease-in-out infinite' }} />
                                </span>
                            )}
                        </div>

                        {/* Artifact chips */}
                        {message.artifacts && message.artifacts.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-4">
                                {message.artifacts.map((artifact) => (
                                    <button
                                        key={artifact.id}
                                        onClick={() => onArtifactClick?.(artifact)}
                                        className="flex items-center gap-2 px-3.5 py-2 rounded-xl
                      text-[12px] font-medium
                      border border-mq-cyan/15 bg-mq-cyan/5
                      text-mq-cyan hover:bg-mq-cyan/10
                      hover:border-mq-cyan/25 hover:scale-[1.02] active:scale-[0.98]
                      transition-all duration-200 cursor-pointer"
                                    >
                                        <ArtifactIcon type={artifact.type} />
                                        <span className="truncate max-w-[200px]">{artifact.title}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

function ArtifactIcon({ type }: { type: string }) {
    const icons: Record<string, string> = { code: '💻', circuit: '🔌', results: '📊' };
    return <span className="text-sm">{icons[type] || '📄'}</span>;
}
