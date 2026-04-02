/* Milimo Quantum — QRNG Operations */
import { useState } from 'react';
import { fetchQRNG } from '../../services/api';

export function QRNGPanel() {
    const [bits, setBits] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [quantumCertified, setQuantumCertified] = useState(false);
    const [length, setLength] = useState(256);

    const fetchEntropy = async () => {
        setLoading(true);
        try {
            const data = await fetchQRNG(length);
            if (data.data) {
                setBits(data.data);
                setQuantumCertified(data.quantum_certified || false);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">🎲 Quantum Randomness (QRNG)</h3>
                <div className="flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${quantumCertified ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`} />
                    <span className="text-[10px] text-green-400 font-mono">
                        {quantumCertified ? 'QUANTUM CERTIFIED' : 'CLASSICAL SIMULATION'}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/20 rounded-lg p-3 border border-white/5">
                    <div className="text-[10px] text-gray-500 uppercase mb-1">Source</div>
                    <div className="text-xs text-white font-medium">
                        {quantumCertified ? 'Qiskit Aer (Quantum)' : 'Qiskit Aer (Monte Carlo)'}
                    </div>
                </div>
                <div className="bg-black/20 rounded-lg p-3 border border-white/5">
                    <div className="text-[10px] text-gray-500 uppercase mb-1">Bit Length</div>
                    <input
                        type="number"
                        value={length}
                        onChange={(e) => setLength(Math.min(10000, Math.max(1, parseInt(e.target.value) || 1)))}
                        className="w-full bg-transparent text-xs text-cyan-400 font-mono focus:outline-none"
                    />
                </div>
            </div>

            <button
                onClick={fetchEntropy}
                disabled={loading}
                className="w-full py-2 bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/20 text-white rounded-lg text-xs font-medium transition-all cursor-pointer disabled:opacity-50"
            >
                {loading ? 'Harvesting Entropy...' : `Generate ${length}-bit Quantum Seed`}
            </button>

            {bits && (
                <div className="p-3 bg-black/40 rounded-lg border border-cyan-500/10 animate-in fade-in duration-500">
                    <div className="text-[9px] text-gray-600 font-mono break-all leading-relaxed">
                        {bits}
                    </div>
                </div>
            )}
        </div>
    );
}
