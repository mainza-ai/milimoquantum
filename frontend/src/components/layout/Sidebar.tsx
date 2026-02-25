/* Milimo Quantum — Sidebar */
import { useState, useEffect } from 'react';
import { AGENTS } from '../../types';
import type { AgentType, HealthStatus } from '../../types';
import { fetchHealth, fetchConversations, deleteConversation } from '../../services/api';

interface ConversationSummary {
    id: string;
    title: string;
    message_count: number;
    updated_at: string;
}

interface SidebarProps {
    isOpen: boolean;
    activeAgent: AgentType;
    onAgentSelect: (agent: AgentType) => void;
    onNewChat: () => void;
    onLoadConversation: (id: string) => void;
    onOpenSettings: () => void;
    onOpenAnalytics?: () => void;
    onOpenSearch?: () => void;
    onOpenMarketplace?: () => void;
    currentConversationId?: string;
}

export function Sidebar({
    isOpen,
    activeAgent,
    onAgentSelect,
    onNewChat,
    onLoadConversation,
    onOpenSettings,
    onOpenAnalytics,
    onOpenSearch,
    onOpenMarketplace,
    currentConversationId,
}: SidebarProps) {
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);

    useEffect(() => {
        fetchHealth().then(setHealth).catch(() => setHealth(null));
        refreshConversations();
        const interval = setInterval(() => {
            fetchHealth().then(setHealth).catch(() => setHealth(null));
            refreshConversations();
        }, 15000);
        return () => clearInterval(interval);
    }, []);

    function refreshConversations() {
        fetchConversations()
            .then((data) => setConversations(data.conversations || []))
            .catch(() => { });
    }

    async function handleDelete(id: string, e: React.MouseEvent) {
        e.stopPropagation();
        await deleteConversation(id);
        refreshConversations();
    }

    return (
        <aside
            className={`${isOpen ? 'w-[260px]' : 'w-0'
                } transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]
      flex flex-col border-r border-mq-border bg-mq-void overflow-hidden shrink-0`}
        >
            {isOpen && (
                <div className="flex flex-col h-full animate-fade-in">
                    {/* Logo header */}
                    <div className="px-5 pt-5 pb-4">
                        <div className="flex items-center gap-3">
                            <img
                                src="/logo_milimo.png"
                                alt="Milimo Quantum"
                                className="w-9 h-9 object-contain drop-shadow-[0_0_8px_rgba(62,207,239,0.3)]"
                            />
                            <div>
                                <h1 className="text-[15px] font-semibold text-mq-text tracking-tight leading-tight">
                                    Milimo Quantum
                                </h1>
                                <p className="text-[10px] text-mq-text-tertiary tracking-[0.12em] uppercase mt-0.5">
                                    Quantum AI
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* New Chat */}
                    <div className="px-3 pb-3">
                        <button
                            onClick={onNewChat}
                            className="w-full py-2 px-4 rounded-xl
                bg-gradient-to-r from-mq-cyan/10 to-mq-teal/10
                border border-mq-border-light
                hover:from-mq-cyan/15 hover:to-mq-teal/15
                hover:border-mq-cyan/20
                text-mq-text text-[13px] font-medium
                transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
                flex items-center gap-2 cursor-pointer group"
                        >
                            <span className="text-mq-cyan group-hover:scale-110 transition-transform duration-200">＋</span>
                            New Conversation
                        </button>
                    </div>

                    {/* Conversation History */}
                    {conversations.length > 0 && (
                        <div className="px-3 pb-3">
                            <p className="text-[10px] text-mq-text-tertiary tracking-[0.14em] uppercase px-2 mb-2 font-medium">
                                History
                            </p>
                            <div className="space-y-px max-h-[180px] overflow-y-auto">
                                {conversations.slice(0, 10).map((c) => (
                                    <button
                                        key={c.id}
                                        onClick={() => onLoadConversation(c.id)}
                                        className={`w-full flex items-center gap-2 py-2 px-3 rounded-lg text-[12px]
                                            transition-all duration-200 cursor-pointer group
                                            ${c.id === currentConversationId
                                                ? 'bg-white/[0.06] text-mq-text'
                                                : 'text-mq-text-secondary hover:text-mq-text hover:bg-white/[0.03]'
                                            }`}
                                    >
                                        <span className="text-[10px] text-[#636370]">💬</span>
                                        <span className="flex-1 text-left truncate">{c.title}</span>
                                        <span
                                            onClick={(e) => handleDelete(c.id, e)}
                                            className="opacity-0 group-hover:opacity-100 text-[10px] text-[#636370]
                                                hover:text-red-400 transition-all cursor-pointer w-4 h-4
                                                flex items-center justify-center rounded"
                                        >✕</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Agents */}
                    <div className="px-3 flex-1 overflow-y-auto">
                        <p className="text-[10px] text-mq-text-tertiary tracking-[0.14em] uppercase px-2 mb-2 font-medium">
                            Agents
                        </p>
                        <div className="space-y-px">
                            {AGENTS.map((agent) => {
                                const isActive = activeAgent === agent.type;
                                return (
                                    <button
                                        key={agent.type}
                                        onClick={() => onAgentSelect(agent.type)}
                                        className={`w-full flex items-center gap-3 py-2.5 px-3 rounded-xl text-[13px]
                      transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] cursor-pointer
                      ${isActive
                                                ? 'glass text-mq-text'
                                                : 'text-mq-text-secondary hover:text-mq-text hover:bg-mq-hover border border-transparent'
                                            }
                      ${isActive ? 'glow-subtle' : ''}`}
                                    >
                                        <span className={`text-[15px] transition-transform duration-200 ${isActive ? 'scale-110' : ''}`}>
                                            {agent.icon}
                                        </span>
                                        <div className="text-left flex-1 min-w-0">
                                            <div className="font-medium leading-tight">{agent.name}</div>
                                            {agent.command && (
                                                <div className="text-[10px] text-mq-text-tertiary font-mono mt-0.5">
                                                    {agent.command}
                                                </div>
                                            )}
                                        </div>
                                        {isActive && (
                                            <div className="w-1.5 h-1.5 rounded-full shrink-0 animate-fade-in"
                                                style={{ backgroundColor: agent.color, boxShadow: `0 0 6px ${agent.color}40` }}
                                            />
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Status + Settings footer */}
                    <div className="px-4 py-3 border-t border-mq-border">
                        <div className="space-y-2">
                            <StatusDot label="Backend" ok={!!health} value={health ? 'Online' : 'Offline'} />
                            <StatusDot label="Ollama" ok={health?.ollama === 'connected'} value={health?.ollama === 'connected' ? 'Ready' : 'Off'} />
                            <StatusDot label="Qiskit" ok={health?.qiskit === 'available'} value={health?.qiskit === 'available' ? 'Ready' : 'N/A'} />
                        </div>
                        <div className="flex gap-1 mt-3">
                            <button
                                onClick={onOpenMarketplace}
                                className="flex-1 py-1.5 px-2 rounded-lg text-[11px]
                                    text-[#636370] hover:text-mq-text hover:bg-white/[0.04]
                                    transition-all flex items-center gap-1.5 cursor-pointer"
                            >
                                <span>🛍️</span> Apps
                            </button>
                            <button
                                onClick={onOpenSearch}
                                className="flex-1 py-1.5 px-2 rounded-lg text-[11px]
                                    text-[#636370] hover:text-mq-text hover:bg-white/[0.04]
                                    transition-all flex items-center gap-1.5 cursor-pointer"
                            >
                                <span>🔍</span> Search
                            </button>
                            <button
                                onClick={onOpenAnalytics}
                                className="flex-1 py-1.5 px-2 rounded-lg text-[11px]
                                    text-[#636370] hover:text-mq-text hover:bg-white/[0.04]
                                    transition-all flex items-center gap-1.5 cursor-pointer"
                            >
                                <span>📊</span> Stats
                            </button>
                        </div>
                        <button
                            onClick={onOpenSettings}
                            className="w-full mt-1 py-1.5 px-3 rounded-lg text-[11px]
                                text-[#636370] hover:text-mq-text hover:bg-white/[0.04]
                                transition-all flex items-center gap-2 cursor-pointer"
                        >
                            <span>⚙</span> Settings
                        </button>
                    </div>
                </div>
            )}
        </aside>
    );
}

function StatusDot({ label, ok, value }: { label: string; ok: boolean; value: string }) {
    return (
        <div className="flex items-center justify-between text-[11px]">
            <span className="text-mq-text-tertiary">{label}</span>
            <div className="flex items-center gap-1.5">
                <span className={`w-[5px] h-[5px] rounded-full ${ok ? 'bg-[#44d8a0]' : 'bg-[#636370]'}`}
                    style={ok ? { boxShadow: '0 0 4px rgba(68,216,160,0.5)' } : {}}
                />
                <span className={ok ? 'text-[#44d8a0]' : 'text-mq-text-tertiary'}>{value}</span>
            </div>
        </div>
    );
}
