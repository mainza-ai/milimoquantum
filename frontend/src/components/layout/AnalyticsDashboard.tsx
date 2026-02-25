/* Milimo Quantum — Analytics Dashboard */
import { useState, useEffect } from 'react';

interface SummaryData {
    conversations: number;
    messages: number;
    projects: number;
    circuits_generated: number;
    agents_used: Record<string, number>;
    top_agent: string | null;
}

interface AgentData {
    agent: string;
    messages: number;
    percentage: number;
}

interface Activity {
    id: string;
    title: string;
    messages: number;
    last_agent: string | null;
    updated_at: string;
}

export function AnalyticsDashboard({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const [summary, setSummary] = useState<SummaryData | null>(null);
    const [agents, setAgents] = useState<AgentData[]>([]);
    const [activities, setActivities] = useState<Activity[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        Promise.all([
            fetch('/api/analytics/summary').then(r => r.json()),
            fetch('/api/analytics/agents').then(r => r.json()),
            fetch('/api/analytics/activity').then(r => r.json()),
        ])
            .then(([sum, ag, act]) => {
                setSummary(sum);
                setAgents(ag.agents || []);
                setActivities(act.activities || []);
            })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [isOpen]);

    if (!isOpen) return null;

    const agentColors: Record<string, string> = {
        research: '#06b6d4',
        chemistry: '#10b981',
        finance: '#f59e0b',
        crypto: '#8b5cf6',
        qml: '#ec4899',
        optimization: '#f97316',
        climate: '#14b8a6',
        code: '#64748b',
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
        w-full max-w-3xl max-h-[85vh] overflow-y-auto mx-4">
                {/* Header */}
                <div className="sticky top-0 z-10 bg-[#0d1117] border-b border-cyan-500/10 px-6 py-4
          flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">📊</span>
                        <h2 className="text-lg font-semibold text-white">Analytics Dashboard</h2>
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
              flex items-center justify-center text-gray-400 hover:text-white
              transition-all cursor-pointer">✕</button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20 text-gray-400">
                        <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                        Loading analytics...
                    </div>
                ) : (
                    <div className="p-6 space-y-6">
                        {/* Stats Cards */}
                        {summary && (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {[
                                    { label: 'Conversations', value: summary.conversations, icon: '💬', color: 'cyan' },
                                    { label: 'Messages', value: summary.messages, icon: '✉️', color: 'blue' },
                                    { label: 'Projects', value: summary.projects, icon: '📁', color: 'green' },
                                    { label: 'Circuits', value: summary.circuits_generated, icon: '⚛️', color: 'purple' },
                                ].map(stat => (
                                    <div key={stat.label}
                                        className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4
                      hover:border-cyan-500/20 transition-all">
                                        <div className="text-2xl mb-1">{stat.icon}</div>
                                        <div className="text-2xl font-bold text-white">{stat.value}</div>
                                        <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Agent Usage Chart */}
                        {agents.length > 0 && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Agent Usage</h3>
                                <div className="space-y-3">
                                    {agents.map(ag => (
                                        <div key={ag.agent} className="flex items-center gap-3">
                                            <div className="w-24 text-xs text-gray-400 capitalize truncate">{ag.agent}</div>
                                            <div className="flex-1 h-6 bg-white/[0.03] rounded-md overflow-hidden relative">
                                                <div
                                                    className="h-full rounded-md transition-all duration-700"
                                                    style={{
                                                        width: `${Math.max(ag.percentage, 2)}%`,
                                                        backgroundColor: agentColors[ag.agent] || '#64748b',
                                                        opacity: 0.8,
                                                    }}
                                                />
                                                <span className="absolute right-2 top-0.5 text-xs text-gray-400">
                                                    {ag.messages}
                                                </span>
                                            </div>
                                            <div className="w-12 text-right text-xs text-gray-500">{ag.percentage}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recent Activity */}
                        {activities.length > 0 && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Recent Activity</h3>
                                <div className="space-y-2">
                                    {activities.slice(0, 8).map(act => (
                                        <div key={act.id}
                                            className="flex items-center gap-3 py-2 px-3 rounded-lg
                        hover:bg-white/[0.03] transition-colors">
                                            <div className="w-2 h-2 rounded-full"
                                                style={{ backgroundColor: agentColors[act.last_agent || ''] || '#64748b' }} />
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm text-gray-300 truncate">{act.title}</div>
                                                <div className="text-xs text-gray-500">
                                                    {act.messages} messages
                                                    {act.last_agent && ` · ${act.last_agent}`}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Empty state */}
                        {(!summary || summary.conversations === 0) && (
                            <div className="text-center py-12 text-gray-500">
                                <div className="text-4xl mb-3">📊</div>
                                <p>No analytics data yet. Start chatting to generate insights!</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
