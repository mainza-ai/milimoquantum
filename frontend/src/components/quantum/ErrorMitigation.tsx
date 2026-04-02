/* Milimo Quantum — Error Mitigation Controls */
import { useState } from 'react';
import { fetchErrorMitigation } from '../../services/api';

export function ErrorMitigation({ circuitName }: { circuitName?: string }) {
    const [method, setMethod] = useState('zne');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleMitigate = async () => {
        if (!circuitName) return;
        setLoading(true);
        try {
            const data = await fetchErrorMitigation(circuitName, method);
            setResult(data);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">🪄 Quantum Error Mitigation</h3>
                <span className="text-[10px] bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full border border-purple-500/20">Active Suppression</span>
            </div>

            {!circuitName ? (
                <p className="text-[11px] text-gray-500 italic">Select a circuit template above to enable mitigation controls.</p>
            ) : (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-3">
                        <div className="space-y-2">
                            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Mitigation Strategy</label>
                            <div className="grid grid-cols-3 gap-2">
                                <MitigationButton
                                    label="ZNE"
                                    active={method === 'zne'}
                                    onClick={() => setMethod('zne')}
                                    subtitle="Zero-Noise Extrap."
                                />
                                <MitigationButton
                                    label="Meas."
                                    active={method === 'measurement'}
                                    onClick={() => setMethod('measurement')}
                                    subtitle="Calibration Matrix"
                                />
                                <MitigationButton
                                    label="Twirl"
                                    active={method === 'twirling'}
                                    onClick={() => setMethod('twirling')}
                                    subtitle="Pauli Twirling"
                                />
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleMitigate}
                        disabled={loading}
                        className="w-full py-2 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 text-purple-400 rounded-lg text-xs font-medium transition-all cursor-pointer disabled:opacity-50"
                    >
                        {loading ? 'Mitigating Noise...' : `Run ${circuitName} with Mitigation`}
                    </button>

        {result && (
            <div className="mt-4 p-3 bg-black/20 border border-purple-500/10 rounded-lg animate-in fade-in zoom-in-95 duration-300">
                <div className="text-[10px] text-gray-500 uppercase mb-2">Improvement vs Raw</div>
                <div className="flex items-center gap-3">
                    <div className="flex-1 space-y-1">
                        <div className="flex justify-between text-[10px]">
                            <span className="text-gray-400">Fidelity</span>
                            <span className="text-green-400">
                                {result.improvement !== undefined
                                    ? `+${(result.improvement * 100).toFixed(1)}%`
                                    : 'N/A'}
                            </span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-green-500/40"
                                style={{ width: result.improvement ? `${Math.min(result.improvement * 100, 100)}%` : '0%' }}
                            />
                        </div>
                    </div>
                </div>
                {result.mitigated_value !== undefined && (
                    <div className="mt-2 text-[10px] text-gray-400">
                        Mitigated value: <span className="text-purple-300 font-mono">{result.mitigated_value.toFixed(6)}</span>
                    </div>
                )}
            </div>
        )}
                </div>
            )}
        </div>
    );
}

function MitigationButton({ label, subtitle, active, onClick }: { label: string; subtitle: string; active: boolean; onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className={`p-2 rounded-lg border text-left transition-all cursor-pointer
                ${active
                    ? 'bg-purple-500/10 border-purple-500/40 text-purple-300'
                    : 'bg-white/[0.02] border-white/[0.06] text-gray-500 hover:border-white/20'
                }`}
        >
            <div className="text-xs font-bold">{label}</div>
            <div className="text-[8px] opacity-60 leading-tight mt-0.5">{subtitle}</div>
        </button>
    );
}
