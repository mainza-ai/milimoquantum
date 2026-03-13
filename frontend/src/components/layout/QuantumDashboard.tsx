/* Milimo Quantum — Quantum Dashboard */
import { useState, useEffect } from 'react';
import { fetchHealth, fetchAnalyticsSummary, fetchQuantumStatus, fetchWithAuth } from '../../services/api';
import { FaultTolerance } from '../quantum/FaultTolerance';
import { ErrorMitigation } from '../quantum/ErrorMitigation';
import { QRNGPanel } from '../quantum/QRNGPanel';
import { HardwareSettings } from '../quantum/HardwareSettings';
import { CircuitBuilder } from '../quantum/CircuitBuilder';
import { BlochSphereInteractive } from '../quantum/BlochSphere';
import { MarketplacePanel } from './MarketplacePanel';
import { WorkflowBuilder } from '../workflow/WorkflowBuilder';
import { AcademyPanel } from '../academy/AcademyPanel';
import { AuditDashboard } from '../admin/AuditDashboard';
import { HPCPortal } from '../hpc/HPCPortal';
import { HardwareBrowser } from '../quantum/HardwareBrowser';
import { HpcJobsPanel } from '../quantum/panels/HpcJobsPanel';

interface DashboardProps {
    isOpen: boolean;
    onClose: () => void;
}

export function QuantumDashboard({ isOpen, onClose }: DashboardProps) {
    const [health, setHealth] = useState<Record<string, unknown> | null>(null);
    const [quantum, setQuantum] = useState<Record<string, unknown> | null>(null);
    const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);
    const [latestResult, setLatestResult] = useState<any>(null);
    const [selectedCircuit, setSelectedCircuit] = useState<string | undefined>();
    const [isMarketplaceOpen, setIsMarketplaceOpen] = useState(false);
    const [isWorkflowOpen, setIsWorkflowOpen] = useState(false);
    const [isAcademyOpen, setIsAcademyOpen] = useState(false);
    const [isAuditOpen, setIsAuditOpen] = useState(false);
    const [isHPCOpen, setIsHPCOpen] = useState(false);
    const [isHardwareOpen, setIsHardwareOpen] = useState(false);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        Promise.all([
            fetchHealth().catch(() => null),
            fetchQuantumStatus().catch(() => null),
            fetchAnalyticsSummary().catch(() => null)
        ]).then(([h, q, s]) => {
            setHealth(h);
            setQuantum(q);
            setSummary(s);
        }).finally(() => setLoading(false));
    }, [isOpen]);

    if (!isOpen) return null;

    const simulators = (quantum as any)?.available_circuits || {};
    const circuitNames = Object.keys(simulators);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
                w-full max-w-4xl max-h-[90vh] overflow-hidden mx-4 flex flex-col"
                style={{ animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
                {/* Header */}
                <div className="sticky top-0 z-10 bg-[#0d1117] border-b border-cyan-500/10 px-6 py-4
                    flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">⚛️</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Quantum Science Hub</h2>
                            <p className="text-xs text-gray-400 mt-0.5">Logical layer, error suppression & hardware orchestration</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={() => setIsMarketplaceOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                text-xs font-medium hover:bg-cyan-500/20 transition-all cursor-pointer flex items-center gap-2">
                            <span>🛍️</span> Marketplace
                        </button>
                        <button onClick={() => setIsWorkflowOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20
                                text-xs font-medium hover:bg-indigo-500/20 transition-all cursor-pointer flex items-center gap-2">
                            <span>⛓️</span> Designer
                        </button>
                        <button onClick={() => setIsAcademyOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20
                                text-xs font-medium hover:bg-emerald-500/20 transition-all cursor-pointer flex items-center gap-2">
                            <span>🎓</span> Academy
                        </button>
                        <button onClick={() => setIsAuditOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20
                                text-xs font-medium hover:bg-red-500/20 transition-all cursor-pointer flex items-center gap-2">
                            <span>🛡️</span> Audit
                        </button>
                        <button onClick={() => setIsHPCOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/20
                                text-xs font-medium hover:bg-orange-500/20 transition-all cursor-pointer flex items-center gap-2">
                            <span>🏎️</span> HPC
                        </button>
                        <button onClick={() => setIsHardwareOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20
                                text-xs font-medium hover:bg-purple-400 transition-all cursor-pointer flex items-center gap-2">
                            <span>🛰️</span> Targets
                        </button>
                        <button onClick={onClose}
                            className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
                                flex items-center justify-center text-gray-400 hover:text-white
                                transition-all cursor-pointer">✕</button>
                    </div>
                </div>

                <MarketplacePanel
                    isOpen={isMarketplaceOpen}
                    onClose={() => setIsMarketplaceOpen(false)}
                />

                <WorkflowBuilder
                    isOpen={isWorkflowOpen}
                    onClose={() => setIsWorkflowOpen(false)}
                />

                <AcademyPanel
                    isOpen={isAcademyOpen}
                    onClose={() => setIsAcademyOpen(false)}
                />

                <AuditDashboard
                    isOpen={isAuditOpen}
                    onClose={() => setIsAuditOpen(false)}
                />

                <HPCPortal
                    isOpen={isHPCOpen}
                    onClose={() => setIsHPCOpen(false)}
                />

                <HardwareBrowser
                    isOpen={isHardwareOpen}
                    onClose={() => setIsHardwareOpen(false)}
                />

                {loading ? (
                    <div className="flex items-center justify-center py-20 text-gray-400">
                        <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                        Initializing Science Environment...
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                        {/* Status & Hardware Section */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-4">
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
                                {summary && (
                                    <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4">
                                        <div className="grid grid-cols-4 gap-2">
                                            <StatBox icon="💬" label="Convs" value={(summary as any).conversations || 0} />
                                            <StatBox icon="✉️" label="Msgs" value={(summary as any).messages || 0} />
                                            <StatBox icon="⚛️" label="Runs" value={(summary as any).circuits_generated || 0} />
                                            <StatBox icon="📁" label="Projs" value={(summary as any).projects || 0} />
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="flex flex-col gap-4">
                                <HardwareSettings />
                                <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 border-l-orange-500/50">
                                    <HpcJobsPanel />
                                </div>
                            </div>
                        </div>

                        {/* Middle Tier: Scientific Visibility */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FaultTolerance />
                            <ErrorMitigation circuitName={selectedCircuit} />
                        </div>

                        {/* Randomness Tier */}
                        <QRNGPanel />

                        {/* Templates Row */}
                        {circuitNames.length > 0 && (
                            <CircuitTemplates
                                circuitNames={circuitNames}
                                simulators={simulators}
                                onSimulationResult={(res) => {
                                    setLatestResult(res);
                                    setSelectedCircuit(res.circuitName as any as string | undefined);
                                }}
                            />
                        )}

                        {/* Circuit Visuals */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
                                <h3 className="text-sm font-medium text-gray-300 mb-4">🛠️ Circuit Builder</h3>
                                <CircuitBuilder onExport={(code: string) => navigator.clipboard.writeText(code)} />
                            </div>

                            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 flex flex-col items-center">
                                <h3 className="text-sm font-medium text-gray-300 mb-4 self-start">🌐 Bloch Sphere</h3>
                                <BlochSphereInteractive
                                    externalTheta={latestResult?.statevector?.theta}
                                    externalPhi={latestResult?.statevector?.phi}
                                    externalLabel={latestResult ? `Result from ${latestResult.circuitName}` : undefined}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ── Executable Circuit Templates ────────────────────── */
function CircuitTemplates({ circuitNames, simulators, onSimulationResult }: { circuitNames: string[]; simulators: Record<string, unknown>; onSimulationResult?: (data: Record<string, unknown>) => void; }) {
    const [running, setRunning] = useState<string | null>(null);
    const [result, setResult] = useState<{ counts?: Record<string, number>; statevector?: { theta: number, phi: number };[key: string]: unknown } | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleRun = async (name: string) => {
        setRunning(name);
        setResult(null);
        setError(null);
        try {
            const res = await fetchWithAuth(`/api/quantum/execute/${name}?shots=1024`);
            const data = await res.json();
            if (data.error) {
                setError(data.error);
            } else {
                const resData = { ...data, circuitName: String(simulators[name]) };
                setResult(resData);
                onSimulationResult?.(resData);
            }
        } catch {
            setError('Execution failed');
        } finally {
            setRunning(null);
        }
    };

    return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4">Available Circuit Templates</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {circuitNames.map(name => (
                    <button key={name}
                        onClick={() => handleRun(name)}
                        disabled={running !== null}
                        className={`px-3 py-2 rounded-lg bg-white/[0.03] border text-left
                            text-sm text-gray-300 font-mono transition-all cursor-pointer
                            ${running === name
                                ? 'border-cyan-500/40 bg-cyan-500/5'
                                : 'border-white/[0.06] hover:border-cyan-500/20 hover:bg-white/[0.05]'
                            } disabled:opacity-60`}
                    >
                        {running === name ? '⏳' : '⚛️'} {String(simulators[name])}
                    </button>
                ))}
            </div>
            {error && (
                <div className="mt-3 text-xs text-red-400 bg-red-500/5 border border-red-500/10 rounded-lg p-3">
                    ❌ {error}
                </div>
            )}
            {result?.counts && (
                <div className="mt-3 bg-black/30 border border-cyan-500/10 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                        <div className="text-[10px] text-gray-500 uppercase tracking-wider">Execution Result</div>
                        {result.statevector && (
                            <div className="text-[10px] text-purple-400 font-mono">
                                θ: {(result.statevector.theta / Math.PI).toFixed(2)}π, φ: {(result.statevector.phi / Math.PI).toFixed(2)}π
                            </div>
                        )}
                    </div>
                    <div className="space-y-1">
                        {Object.entries(result.counts)
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 8)
                            .map(([state, count]) => (
                                <div key={state} className="flex items-center gap-2 text-xs">
                                    <span className="font-mono text-cyan-400">|{state}⟩</span>
                                    <div className="flex-1 h-3 bg-white/[0.03] rounded-full overflow-hidden">
                                        <div className="h-full bg-cyan-500/50 rounded-full"
                                            style={{ width: `${(count / 1024) * 100}%` }} />
                                    </div>
                                    <span className="text-gray-500 tabular-nums w-10 text-right">{count}</span>
                                </div>
                            ))}
                    </div>
                </div>
            )}
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
