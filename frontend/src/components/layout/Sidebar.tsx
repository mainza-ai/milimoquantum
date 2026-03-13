/* Milimo Quantum — Sidebar (Claude-inspired minimal design) */
import { useState, useEffect, useRef, useCallback } from 'react';
import { AGENTS } from '../../types';
import type { AgentType, HealthStatus } from '../../types';
import { fetchHealth, fetchConversations, deleteConversation } from '../../services/api';
import { useProject } from '../../contexts/ProjectContext';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { extensionRegistry } from '../../extensions/registry';

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
    currentConversationId?: string;
}

/* ── Agent category grouping ── */
const AGENT_CATEGORIES = [
    {
        label: 'Core',
        agents: ['orchestrator', 'code', 'research', 'planning'],
    },
    {
        label: 'Science',
        agents: ['chemistry', 'climate', 'sensing'],
    },
    {
        label: 'Industry',
        agents: ['finance', 'optimization', 'crypto', 'dwave'],
    },
    {
        label: 'Advanced',
        agents: ['qml', 'qgi', 'networking'],
    },
];

export function Sidebar({
    isOpen,
    activeAgent,
    onAgentSelect,
    onNewChat,
    onLoadConversation,
    currentConversationId,
}: SidebarProps) {
    const { openExtension } = useWorkspace();
    const { activeProjectId, activeProject, clearActiveProject } = useProject();
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [agentPickerOpen, setAgentPickerOpen] = useState(false);
    const pickerRef = useRef<HTMLDivElement>(null);

    const refreshConversations = useCallback(() => {
        fetchConversations(activeProjectId)
            .then((data) => setConversations(data.conversations || []))
            .catch(() => { });
    }, [activeProjectId]);

    useEffect(() => {
        fetchHealth().then(setHealth).catch(() => setHealth(null));
        refreshConversations();
        const interval = setInterval(() => {
            fetchHealth().then(setHealth).catch(() => setHealth(null));
            refreshConversations();
        }, 15000);
        return () => clearInterval(interval);
    }, [refreshConversations]);

    // Close agent picker on outside click
    useEffect(() => {
        function handleClick(e: MouseEvent) {
            if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
                setAgentPickerOpen(false);
            }
        }
        if (agentPickerOpen) document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, [agentPickerOpen]);

    async function handleDelete(id: string, e: React.MouseEvent) {
        e.stopPropagation();
        await deleteConversation(id);
        refreshConversations();
    }

    const activeAgentInfo = AGENTS.find((a) => a.type === activeAgent) || AGENTS[0];
    const isHealthy = !!health;

    return (
        <aside
            className={`${isOpen ? 'w-[260px]' : 'w-0'
                } transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]
      flex flex-col border-r border-white/[0.06] bg-[#0a0a0f] overflow-hidden shrink-0`}
        >
            {isOpen && (
                <div className="flex flex-col h-full animate-fade-in">

                    {/* ── Logo header ── */}
                    <div className="px-4 pt-5 pb-3">
                        <div className="flex items-center gap-3">
                            <img
                                src="/logo_milimo.png"
                                alt="Milimo Quantum"
                                className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(62,207,239,0.3)]"
                            />
                            <div>
                                <h1 className="text-[14px] font-semibold text-[#e8e8ed] tracking-tight leading-tight">
                                    Milimo Quantum
                                </h1>
                                <p className="text-[9px] text-[#505060] tracking-[0.12em] uppercase mt-0.5">
                                    Quantum AI
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* ── Header: New Chat ── */}
                    <div className="px-3 pt-4 pb-2">
                        <button
                            onClick={onNewChat}
                            className="w-full py-2.5 px-4 rounded-xl
                                bg-white/[0.04] hover:bg-[#3ecfef]/5
                                border border-white/[0.06] hover:border-[#3ecfef]/30
                                text-[#e8e8ed] text-[13px] font-medium
                                transition-all duration-300 hover:shadow-[0_0_15px_rgba(62,207,239,0.15)]
                                flex items-center gap-2.5 cursor-pointer group"
                        >
                            <svg className="w-4 h-4 text-[#8a8a9a] group-hover:text-[#b0b0c0] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                            </svg>
                            New chat
                        </button>
                    </div>

                    {/* ── Active Project Badge ── */}
                    {activeProject && (
                        <div className="px-3 pb-2">
                            <div className="flex items-center justify-between px-3 py-2 rounded-xl
                                bg-cyan-500/10 border border-cyan-500/20 group/proj">
                                <div className="flex items-center gap-2 min-w-0">
                                    <span className="text-xs">📁</span>
                                    <div className="flex flex-col min-w-0">
                                        <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider leading-none">Project</span>
                                        <span className="text-[12px] text-white font-medium truncate leading-tight mt-0.5">{activeProject.name}</span>
                                    </div>
                                </div>
                                <button 
                                    onClick={clearActiveProject}
                                    className="w-5 h-5 rounded-md hover:bg-cyan-500/20 flex items-center justify-center
                                        text-cyan-400/50 hover:text-cyan-400 transition-all opacity-0 group-hover/proj:opacity-100 cursor-pointer"
                                    title="Clear Active Project"
                                >✕</button>
                            </div>
                        </div>
                    )}

                    {/* ── Agent Selector (compact) ── */}
                    <div className="px-3 pb-2 relative" ref={pickerRef}>
                        <button
                            onClick={() => setAgentPickerOpen(!agentPickerOpen)}
                            className="w-full py-2 px-3 rounded-lg
                                hover:bg-white/[0.04]
                                text-[12px] font-medium
                                transition-all duration-200
                                flex items-center gap-2 cursor-pointer"
                        >
                            <span className="text-[14px]">{activeAgentInfo.icon}</span>
                            <span className="text-[#b0b0c0] flex-1 text-left">{activeAgentInfo.name}</span>
                            <svg className={`w-3 h-3 text-[#636370] transition-transform duration-200 ${agentPickerOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                            </svg>
                        </button>

                        {/* Agent dropdown */}
                        {agentPickerOpen && (
                            <div className="absolute left-3 right-3 top-full mt-1 z-50
                                bg-[#18181f] border border-white/[0.08] rounded-xl
                                shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden
                                animate-fade-in">
                                <div className="py-1.5 max-h-[360px] overflow-y-auto">
                                    {AGENT_CATEGORIES.map((cat) => (
                                        <div key={cat.label}>
                                            <div className="px-3 pt-2.5 pb-1 text-[9px] text-[#505060] uppercase tracking-[0.12em] font-semibold">
                                                {cat.label}
                                            </div>
                                            {cat.agents.map((agentType) => {
                                                const agent = AGENTS.find((a) => a.type === agentType);
                                                if (!agent) return null;
                                                const isActive = activeAgent === agent.type;
                                                return (
                                                    <button
                                                        key={agent.type}
                                                        onClick={() => {
                                                            onAgentSelect(agent.type);
                                                            setAgentPickerOpen(false);
                                                        }}
                                                        className={`w-full flex items-center gap-2.5 py-2 px-3 text-[12px]
                                                            transition-all duration-150 cursor-pointer
                                                            ${isActive
                                                                ? 'bg-white/[0.06] text-[#e8e8ed]'
                                                                : 'text-[#8a8a9a] hover:text-[#c0c0d0] hover:bg-white/[0.03]'
                                                            }`}
                                                    >
                                                        <span className="text-[13px] w-5 text-center">{agent.icon}</span>
                                                        <span className="flex-1 text-left">{agent.name}</span>
                                                        {agent.command && (
                                                            <span className="text-[9px] text-[#404050] font-mono">{agent.command}</span>
                                                        )}
                                                        {isActive && (
                                                            <div className="w-1.5 h-1.5 rounded-full bg-[#3ecfef]"
                                                                style={{ boxShadow: '0 0 6px rgba(62,207,239,0.4)' }}
                                                            />
                                                        )}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Divider ── */}
                    <div className="mx-4 border-t border-white/[0.04]" />

                    {/* ── Conversations ── */}
                    <div className="flex-1 overflow-y-auto px-2 pt-3">
                        {conversations.length > 0 ? (
                            <div className="space-y-0.5">
                                {conversations.slice(0, 30).map((c) => {
                                    const isActive = c.id === currentConversationId;
                                    return (
                                        <button
                                            key={c.id}
                                            onClick={() => onLoadConversation(c.id)}
                                            className={`w-full flex items-center gap-2 py-2 px-3 rounded-lg text-[13px]
                                                transition-all duration-150 cursor-pointer group text-left
                                                ${isActive
                                                    ? 'bg-white/[0.06] text-[#e8e8ed] border-l-2 border-[#3ecfef]'
                                                    : 'text-[#8a8a9a] border-l-2 border-transparent hover:text-[#c0c0d0] hover:bg-[#3ecfef]/[0.02] hover:border-[#3ecfef]/50'
                                                }`}
                                        >
                                            <span className="flex-1 truncate leading-snug">{c.title}</span>
                                            <span
                                                onClick={(e) => handleDelete(c.id, e)}
                                                className="opacity-0 group-hover:opacity-100 text-[11px] text-[#505060]
                                                    hover:text-red-400 transition-all cursor-pointer
                                                    w-5 h-5 flex items-center justify-center rounded-md
                                                    hover:bg-white/[0.06]"
                                            >
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="px-3 py-8 text-center">
                                <p className="text-[12px] text-[#404050]">No conversations yet</p>
                            </div>
                        )}
                    </div>

                    {/* ── Footer ── */}
                    <div className="px-3 py-3 border-t border-white/[0.04]">
                        {/* Status indicator */}
                        <div className="flex items-center gap-2 px-2 mb-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-[#34d399]' : 'bg-[#636370]'}`}
                                style={isHealthy ? { boxShadow: '0 0 6px rgba(52,211,153,0.4)' } : {}}
                            />
                            <span className="text-[11px] text-[#505060]">
                                {isHealthy ? 'Connected' : 'Offline'}
                            </span>
                        </div>

                        {/* Quick access icons */}
                        <div className="flex items-center gap-0.5 mb-1">
                            {['mqdd', 'autoresearch', 'search', 'analytics', 'projects', 'dashboard', 'academy', 'marketplace'].map(id => {
                                const ext = extensionRegistry.get(id);
                                if (!ext) return null;
                                return (
                                    <FooterButton key={id} icon={ext.icon} label={ext.name} onClick={() => openExtension(id)} />
                                );
                            })}
                        </div>

                        {/* Settings */}
                        <button
                            onClick={() => openExtension('settings')}
                            className="w-full py-2 px-3 rounded-lg text-[12px]
                                text-[#8a8a9a] hover:text-[#c0c0d0] hover:bg-white/[0.04]
                                transition-all duration-150 flex items-center gap-2.5 cursor-pointer"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            Settings
                        </button>
                    </div>
                </div>
            )}
        </aside>
    );
}

function FooterButton({ icon, label, onClick }: { icon: string; label: string; onClick?: () => void }) {
    return (
        <button
            onClick={onClick}
            title={label}
            className="flex-1 py-1.5 rounded-md text-[13px]
                text-[#505060] hover:text-[#8a8a9a] hover:bg-white/[0.04]
                transition-all duration-150 flex items-center justify-center cursor-pointer"
        >
            {icon}
        </button>
    );
}
