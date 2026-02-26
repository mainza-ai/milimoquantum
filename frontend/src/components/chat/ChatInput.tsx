/* Milimo Quantum — Chat Input */
import { useState, useRef, useEffect, useCallback } from 'react';
import type { AgentType } from '../../types';
import { AGENTS } from '../../types';

interface ChatInputProps {
    onSend: (message: string, fileId?: string) => void;
    isStreaming: boolean;
    activeAgent: AgentType;
}

export function ChatInput({ onSend, isStreaming, activeAgent }: ChatInputProps) {
    const [value, setValue] = useState('');
    const [showCommands, setShowCommands] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const [fileName, setFileName] = useState<string | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

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
        const fileId = textareaRef.current?.getAttribute('data-file-id') || undefined;
        onSend(value, fileId);
        setFileName(null);
        setValue('');
        textareaRef.current?.removeAttribute('data-file-id');
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

    // ── File upload handling ─────────────────────────
    const handleFile = useCallback(async (file: File) => {
        const ext = file.name.split('.').pop()?.toLowerCase();
        if (!['qasm', 'py', 'qpy', 'txt', 'csv', 'pdf', 'json'].includes(ext || '')) {
            return; // unsupported file type
        }
        setFileName(file.name);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/chat/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.id) {
                // Attach to context
                const prefix = ext === 'qasm'
                    ? `Execute this QASM circuit:\n\n`
                    : `Analyze this file:\n\n`;
                setValue(prev => {
                    const spacer = prev ? prev + '\n\n' : '';
                    return spacer + prefix + '[Attached File: ' + file.name + ']';
                });
                // We store the file ID on the element or in state temporarily so it can be sent
                textareaRef.current?.setAttribute('data-file-id', data.id);
                textareaRef.current?.focus();
            }
        } catch (e) {
            console.error("Upload failed", e);
            setFileName(null);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
        e.target.value = ''; // reset for re-select
    }, [handleFile]);

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
                    className={`flex items-end gap-3 glass rounded-2xl p-3
            focus-within:border-mq-cyan/20 transition-all duration-300
            glow-inset ${dragOver ? 'border-mq-cyan/40 bg-mq-cyan/5' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
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
                        placeholder={dragOver
                            ? "Drop .qasm or .py file here..."
                            : "Message Milimo Quantum... (type / for commands)"}
                        rows={1}
                        className="flex-1 bg-transparent text-mq-text placeholder-mq-text-tertiary
              text-[14px] resize-none outline-none max-h-[180px] leading-relaxed"
                        disabled={isStreaming}
                    />

                    {/* File name badge */}
                    {fileName && (
                        <span className="text-[10px] text-mq-cyan bg-mq-cyan/10 px-2 py-0.5 rounded-lg shrink-0 mb-1">
                            📄 {fileName}
                        </span>
                    )}

                    {/* Upload button */}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".qasm,.py,.qpy,.txt"
                        className="hidden"
                        onChange={handleFileSelect}
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0
              bg-mq-elevated/50 text-mq-text-tertiary hover:text-mq-cyan hover:bg-mq-cyan/10
              transition-all duration-200 cursor-pointer mb-0.5"
                        title="Upload .qasm, .py, or .qpy file"
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                        </svg>
                    </button>

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

