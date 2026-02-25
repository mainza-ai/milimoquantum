/* Milimo Quantum — Chat Input */
import { useState, useRef, useEffect } from 'react';
import type { AgentType } from '../../types';
import { AGENTS } from '../../types';

interface ChatInputProps {
    onSend: (message: string) => void;
    isStreaming: boolean;
    activeAgent: AgentType;
}

export function ChatInput({ onSend, isStreaming, activeAgent }: ChatInputProps) {
    const [value, setValue] = useState('');
    const [showCommands, setShowCommands] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const agent = AGENTS.find((a) => a.type === activeAgent);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
        }
    }, [value]);

    const handleSubmit = () => {
        if (!value.trim() || isStreaming) return;
        setShowCommands(false);
        onSend(value);
        setValue('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
        if (e.key === '/' && value === '') setShowCommands(true);
        if (e.key === 'Escape') setShowCommands(false);
    };

    const handleCommandSelect = (cmd: string) => {
        setValue(cmd + ' ');
        setShowCommands(false);
        textareaRef.current?.focus();
    };

    return (
        <div className="px-5 pb-5 pt-2">
            <div className="max-w-[720px] mx-auto relative">
                {/* Slash command palette */}
                {showCommands && (
                    <>
                        {/* Click-outside backdrop to dismiss */}
                        <div
                            className="fixed inset-0 z-10"
                            onClick={() => setShowCommands(false)}
                        />
                        <div className="absolute bottom-full mb-2 left-0 right-0 glass-strong rounded-2xl p-2 z-20 animate-fade-in-scale glow-subtle">
                            <p className="text-[10px] text-mq-text-tertiary tracking-[0.14em] uppercase px-3 py-1.5 font-medium">
                                Commands
                            </p>
                            {AGENTS.filter((a) => a.command).map((a) => (
                                <button
                                    key={a.type}
                                    onClick={() => handleCommandSelect(a.command)}
                                    className="w-full flex items-center gap-3 py-2.5 px-3 rounded-xl
                      text-[13px] text-mq-text-secondary hover:bg-mq-hover
                      hover:text-mq-text transition-all duration-200 cursor-pointer"
                                >
                                    <span className="text-[15px]">{a.icon}</span>
                                    <span className="font-mono text-mq-cyan text-xs">{a.command}</span>
                                    <span className="text-[11px] text-mq-text-tertiary flex-1 text-right">{a.description}</span>
                                </button>
                            ))}
                        </div>
                    </>
                )}

                {/* Input container */}
                <div
                    className="flex items-end gap-3 glass rounded-2xl p-3
            focus-within:border-mq-cyan/20 transition-all duration-300
            glow-inset"
                >
                    {/* Agent icon */}
                    <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-sm shrink-0 mb-0.5
              transition-all duration-200"
                        style={{ backgroundColor: `${agent?.color}10`, color: agent?.color }}
                    >
                        {agent?.icon}
                    </div>

                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => {
                            setValue(e.target.value);
                            if (!e.target.value.startsWith('/')) setShowCommands(false);
                        }}
                        onKeyDown={handleKeyDown}
                        placeholder="Message Milimo Quantum... (type / for commands)"
                        rows={1}
                        className="flex-1 bg-transparent text-mq-text placeholder-mq-text-tertiary
              text-[14px] resize-none outline-none max-h-[180px] leading-relaxed"
                        disabled={isStreaming}
                    />

                    {/* Send */}
                    <button
                        onClick={handleSubmit}
                        disabled={!value.trim() || isStreaming}
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0
              transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] cursor-pointer mb-0.5
              ${value.trim() && !isStreaming
                                ? 'bg-mq-cyan text-mq-black hover:scale-110 active:scale-95'
                                : 'bg-mq-elevated/50 text-mq-text-tertiary'
                            }`}
                        style={value.trim() && !isStreaming ? { boxShadow: '0 0 16px rgba(62,207,239,0.3)' } : {}}
                    >
                        {isStreaming ? (
                            <div className="flex gap-[3px]">
                                <div className="w-[3px] h-[3px] rounded-full bg-current typing-dot" />
                                <div className="w-[3px] h-[3px] rounded-full bg-current typing-dot" />
                                <div className="w-[3px] h-[3px] rounded-full bg-current typing-dot" />
                            </div>
                        ) : (
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                            </svg>
                        )}
                    </button>
                </div>

                <p className="text-center text-[10px] text-mq-text-tertiary/50 mt-2.5 tracking-wide">
                    Powered by Qiskit · Ollama · Open Source
                </p>
            </div>
        </div>
    );
}
