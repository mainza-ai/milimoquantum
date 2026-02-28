/* Milimo Quantum — Fault Tolerance & Resource Estimation */
import { useState } from 'react';
import { fetchFaultTolerantResource } from '../../services/api';

export function FaultTolerance() {
    const [algo, setAlgo] = useState('shor');
    const [size, setSize] = useState(1024);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleEstimate = async () => {
        setLoading(true);
        try {
            const data = await fetchFaultTolerantResource(algo, size);
            setResult(data);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">🛡️ Fault Tolerance & Resource Estimation</h3>
                <span className="text-[10px] bg-red-500/10 text-red-400 px-2 py-0.5 rounded-full border border-red-500/20">Logical Layer</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                    <label className="text-[10px] text-gray-500 uppercase tracking-wider">Algorithm</label>
                    <select
                        value={algo}
                        onChange={(e) => setAlgo(e.target.value)}
                        className="w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-gray-300 outline-none focus:border-cyan-500/50 transition-all"
                    >
                        <option value="shor">Shor's Factoring</option>
                        <option value="grover">Grover Search</option>
                        <option value="chemistry">VQE (Chemistry)</option>
                    </select>
                </div>
                <div className="space-y-1">
                    <label className="text-[10px] text-gray-500 uppercase tracking-wider">Problem Size (bits/qubits)</label>
                    <input
                        type="number"
                        value={size}
                        onChange={(e) => setSize(parseInt(e.target.value))}
                        className="w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-gray-300 outline-none focus:border-cyan-500/50 transition-all"
                    />
                </div>
            </div>

            <button
                onClick={handleEstimate}
                disabled={loading}
                className="w-full py-2 bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium transition-all cursor-pointer disabled:opacity-50"
            >
                {loading ? 'Calculating...' : 'Run Estimation'}
            </button>

            {result && !result.error && (
                <div className="mt-4 p-4 bg-black/20 border border-cyan-500/10 rounded-lg space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-[10px] text-gray-500 uppercase">Physical Qubits</div>
                            <div className="text-lg font-bold text-white">{result.physical_qubits?.toLocaleString()}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-gray-500 uppercase">Runtime (Est.)</div>
                            <div className="text-lg font-bold text-white">{result.runtime_days?.toFixed(2)} Days</div>
                        </div>
                    </div>
                    <div className="pt-2 border-t border-white/5">
                        <div className="text-[10px] text-gray-500 uppercase mb-1">Code Distance Required</div>
                        <div className="flex items-center gap-2">
                            <div className="h-2 flex-1 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-cyan-500/40" style={{ width: `${(result.code_distance / 31) * 100}%` }} />
                            </div>
                            <span className="text-xs font-mono text-cyan-400">{result.code_distance}</span>
                        </div>
                    </div>
                </div>
            )}

            {result?.error && (
                <div className="text-xs text-red-400 p-2 bg-red-500/5 border border-red-500/10 rounded-lg">
                    ⚠️ {result.error}
                </div>
            )}
        </div>
    );
}
