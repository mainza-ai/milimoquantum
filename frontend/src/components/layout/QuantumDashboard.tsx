/* Milimo Quantum — Quantum Dashboard */
import { useState, useEffect } from 'react';
import { fetchHealth, fetchAnalyticsSummary, fetchCircuitStats, fetchQuantumStatus } from '../../services/api';
import { CircuitBuilder } from '../quantum/CircuitBuilder';
import { BlochSphereInteractive } from '../quantum/BlochSphere';

interface DashboardProps {
    isOpen: boolean;
    onClose: () => void;
}

export function QuantumDashboard({ isOpen, onClose }: DashboardProps) {
    const [health, setHealth] = useState<Record<string, unknown> | null>(null);
    const [quantum, setQuantum] = useState<Record<string, unknown> | null>(null);
    const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
    const [circuits, setCircuits] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        Promise.all([
            fetchHealth().catch(() => null),
            fetchQuantumStatus().catch(() => null),
            fetchAnalyticsSummary().catch(() => null),
            fetchCircuitStats().catch(() => null),
        ]).then(([h, q, s, c]) => {
            setHealth(h);
            setQuantum(q);
            setSummary(s);
            setCircuits(c);
        }).finally(() => setLoading(false));
    }, [isOpen]);

    if (!isOpen) return null;

    const simulators = (quantum as any)?.available_circuits || {};
    const circuitNames = Object.keys(simulators);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
                w-full max-w-3xl max-h-[85vh] overflow-hidden mx-4 flex flex-col"
                style={{ animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
                {/* Header */}
                <div className="sticky top-0 z-10 bg-[#0d1117] border-b border-cyan-500/10 px-6 py-4
                    flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">⚛️</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Quantum Dashboard</h2>
                            <p className="text-xs text-gray-400 mt-0.5">System status & circuit overview</p>
                        </div>
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
                            flex items-center justify-center text-gray-400 hover:text-white
                            transition-all cursor-pointer">✕</button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20 text-gray-400">
                        <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                        Loading dashboard...
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {/* System Status Row */}
                        <div className="grid grid-cols-3 gap-3">
                            <StatusCard
                                icon="🟢"
                                label="Backend"
                                value={health?.status === 'healthy' ? 'Online' : 'Offline'}
                                ok={health?.status === 'healthy'}
                            />
                            <StatusCard
                                icon="🤖"
                                label="Ollama"
                                value={health?.ollama === 'connected' ? 'Connected' : 'Disconnected'}
                                ok={health?.ollama === 'connected'}
                            />
                            <StatusCard
                                icon="⚛️"
                                label="Qiskit"
                                value={health?.qiskit === 'available' ? 'Available' : 'Not Available'}
                                ok={health?.qiskit === 'available'}
                            />
                        </div>

                        {/* Usage Stats */}
                        {summary && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Usage Statistics</h3>
                                <div className="grid grid-cols-4 gap-3">
                                    <StatBox icon="💬" label="Conversations" value={(summary as any).conversations || 0} />
                                    <StatBox icon="✉️" label="Messages" value={(summary as any).messages || 0} />
                                    <StatBox icon="⚛️" label="Circuits Run" value={(summary as any).circuits_generated || 0} />
                                    <StatBox icon="📁" label="Projects" value={(summary as any).projects || 0} />
                                </div>
                            </div>
                        )}

                        {/* Circuit Stats */}
                        {circuits && (circuits as any).total_circuits > 0 && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Circuit Metrics</h3>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Qubit Range</div>
                                        <div className="text-lg font-bold text-white">
                                            {(circuits as any).qubit_distribution.min}–{(circuits as any).qubit_distribution.max}
                                        </div>
                                        <div className="text-[10px] text-gray-500">
                                            Avg: {(circuits as any).qubit_distribution.avg}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Circuit Depth</div>
                                        <div className="text-lg font-bold text-white">
                                            {(circuits as any).depth_distribution.min}–{(circuits as any).depth_distribution.max}
                                        </div>
                                        <div className="text-[10px] text-gray-500">
                                            Avg: {(circuits as any).depth_distribution.avg}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Total Circuits</div>
                                        <div className="text-lg font-bold text-cyan-400">
                                            {(circuits as any).total_circuits}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Available Circuits */}
                        {circuitNames.length > 0 && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Available Circuit Templates</h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                    {circuitNames.map(name => (
                                        <div key={name}
                                            className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]
                                                text-sm text-gray-300 font-mono hover:border-cyan-500/20 transition-all"
                                        >
                                            ⚛️ {simulators[name]}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Top Agents */}
                        {summary && (summary as any).agents_used && Object.keys((summary as any).agents_used).length > 0 && (
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">Most Used Agents</h3>
                                <div className="space-y-2">
                                    {Object.entries((summary as any).agents_used).slice(0, 5).map(([agent, count]) => {
                                        const total = Object.values((summary as any).agents_used as Record<string, number>)
                                            .reduce((a: number, b: number) => a + b, 0);
                                        const pct = total > 0 ? ((count as number) / total) * 100 : 0;
                                        return (
                                            <div key={agent} className="flex items-center gap-3">
                                                <div className="w-20 text-xs text-gray-400 capitalize truncate">{agent}</div>
                                                <div className="flex-1 h-5 bg-white/[0.03] rounded-md overflow-hidden relative">
                                                    <div
                                                        className="h-full rounded-md bg-cyan-500/60 transition-all duration-700"
                                                        style={{ width: `${Math.max(pct, 3)}%` }}
                                                    />
                                                    <span className="absolute right-2 top-0 text-[10px] text-gray-400">
                                                        {count as number}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Tools: Circuit Builder & Bloch Sphere */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Circuit Builder */}
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">🛠️ Circuit Builder</h3>
                                <CircuitBuilder onExport={(code) => navigator.clipboard.writeText(code)} />
                            </div>

                            {/* Bloch Sphere */}
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 flex flex-col items-center">
                                <h3 className="text-sm font-medium text-gray-300 mb-4 self-start">🌐 Bloch Sphere</h3>
                                <BlochSphereInteractive />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatusCard({ icon, label, value, ok }: { icon: string; label: string; value: string; ok: boolean }) {
    return (
        <div className={`rounded-xl p-4 border transition-all
            ${ok
                ? 'bg-green-500/[0.03] border-green-500/10'
                : 'bg-red-500/[0.03] border-red-500/10'
            }`}
        >
            <div className="text-lg mb-1">{icon}</div>
            <div className={`text-sm font-semibold ${ok ? 'text-green-400' : 'text-red-400'}`}>{value}</div>
            <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
        </div>
    );
}

function StatBox({ icon, label, value }: { icon: string; label: string; value: number }) {
    return (
        <div className="text-center">
            <div className="text-lg mb-1">{icon}</div>
            <div className="text-xl font-bold text-white">{value}</div>
            <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
        </div>
    );
}
