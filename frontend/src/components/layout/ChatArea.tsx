/* Milimo Quantum — Chat Area */
import { useRef, useEffect } from 'react';
import { MessageBubble } from '../chat/MessageBubble';
import { ChatInput } from '../chat/ChatInput';
import type { ChatMessage, Artifact, AgentType } from '../../types';
import { AGENTS } from '../../types';

interface ChatAreaProps {
    messages: ChatMessage[];
    isStreaming: boolean;
    activeAgent: AgentType;
    onSend: (message: string, fileId?: string) => void;
    onArtifactClick: (artifact: Artifact) => void;
}

export function ChatArea({
    messages,
    isStreaming,
    activeAgent,
    onSend,
    onArtifactClick,
}: ChatAreaProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages]);

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-mq-black relative">
            {/* Subtle ambient gradient */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px]
          bg-[radial-gradient(ellipse_at_center,_rgba(62,207,239,0.03)_0%,_transparent_70%)]" />
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto relative z-10">
                {messages.length === 0 ? (
                    <WelcomeScreen onSend={onSend} />
                ) : (
                    <div className="max-w-[720px] mx-auto py-8 px-5 space-y-8">
                        {messages.map((msg) => (
                            <MessageBubble
                                key={msg.id}
                                message={msg}
                                onArtifactClick={onArtifactClick}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="relative z-10">
                <ChatInput onSend={onSend} isStreaming={isStreaming} activeAgent={activeAgent} />
            </div>
        </div>
    );
}

function WelcomeScreen({ onSend }: { onSend: (msg: string, fileId?: string) => void }) {
    const suggestions = [
        { icon: '⚛', text: 'What is quantum computing?', gradient: 'from-mq-cyan/8 to-mq-teal/8' },
        { icon: '💻', text: '/code Create a Bell state circuit', gradient: 'from-mq-cyan/6 to-mq-ice/8' },
        { icon: '📚', text: '/research Explain superposition', gradient: 'from-mq-teal/6 to-mq-cyan/8' },
        { icon: '⚡', text: '/code Create a GHZ state with 5 qubits', gradient: 'from-mq-ice/6 to-mq-cyan/6' },
    ];

    return (
        <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-lg px-6 animate-fade-in-up">
                {/* Logo with glow */}
                <div className="relative mb-10 inline-block">
                    <img
                        src="/logo_milimo.png"
                        alt="Milimo Quantum"
                        className="w-20 h-20 mx-auto animate-float drop-shadow-[0_0_20px_rgba(62,207,239,0.25)]"
                    />
                    {/* Glow ring */}
                    <div className="absolute inset-0 w-20 h-20 mx-auto rounded-full
            bg-mq-cyan/5 blur-2xl" />
                </div>

                <h2 className="text-3xl font-bold text-mq-text tracking-tight mb-3
          bg-gradient-to-r from-mq-text via-mq-cyan to-mq-text bg-clip-text"
                    style={{ backgroundSize: '200% 100%' }}
                >
                    Welcome to Milimo Quantum
                </h2>
                <p className="text-mq-text-secondary text-[15px] leading-relaxed mb-10 max-w-md mx-auto">
                    The Universe of Quantum, In One Place. Build circuits, run simulations,
                    and explore quantum algorithms with AI.
                </p>

                {/* Suggestion cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {suggestions.map((s, i) => (
                        <button
                            key={i}
                            type="button"
                            onClick={(e) => { e.preventDefault(); onSend(s.text); }}
                            className={`flex items-center gap-3 px-4 py-3.5 rounded-2xl
                bg-gradient-to-br ${s.gradient}
                border border-mq-border hover:border-mq-border-light
                transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
                text-left group cursor-pointer
                hover:scale-[1.02] active:scale-[0.98]
                glow-inset`}
                            style={{ animationDelay: `${i * 0.08}s` }}
                        >
                            <span className="text-lg group-hover:scale-110 transition-transform duration-200">{s.icon}</span>
                            <span className="text-[13px] text-mq-text-secondary group-hover:text-mq-text transition-colors duration-300">
                                {s.text}
                            </span>
                        </button>
                    ))}
                </div>

                {/* Agent badges */}
                <div className="flex justify-center gap-2 mt-10 flex-wrap">
                    {AGENTS.filter((a) => a.command).map((a) => (
                        <span
                            key={a.type}
                            className="text-[10px] px-3 py-1 rounded-full border border-mq-border
                text-mq-text-tertiary tracking-wide hover:border-mq-border-light
                transition-colors duration-300"
                        >
                            {a.icon} {a.command}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}
