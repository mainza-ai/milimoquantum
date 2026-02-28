/* Milimo Quantum — Hardware & Execution Settings */
import { useState, useEffect } from 'react';
import { fetchHardwareProviders } from '../../services/api';

export function HardwareSettings() {
    const [providers, setProviders] = useState<any>(null);
    const [selected, setSelected] = useState('aer');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchHardwareProviders()
            .then(data => {
                setProviders(data.providers);
                setLoading(false);
            });
    }, []);

    if (loading) return null;

    return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">⚙️ Hardware Backend Selection</h3>
                <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Global Override</span>
            </div>

            <div className="grid grid-cols-1 gap-2">
                {providers && Object.entries(providers).map(([id, p]: [string, any]) => (
                    <button
                        key={id}
                        onClick={() => setSelected(id)}
                        className={`group flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer
                            ${selected === id
                                ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-200'
                                : 'bg-transparent border-white/[0.05] text-gray-500 hover:border-white/10 hover:bg-white/[0.01]'
                            }`}
                    >
                        <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${p.available ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 'bg-gray-600'}`} />
                            <div className="text-left">
                                <div className={`text-xs font-semibold ${selected === id ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'}`}>{p.name}</div>
                                <div className="text-[9px] opacity-60 uppercase">{p.type} cluster</div>
                            </div>
                        </div>
                        {selected === id && <div className="text-xs text-cyan-400">ACTIVE</div>}
                    </button>
                ))}
            </div>

            <div className="p-3 bg-blue-500/5 border border-blue-500/10 rounded-lg">
                <p className="text-[10px] text-blue-300/80 leading-relaxed italic">
                    Note: "HPC Cluster" is currently simulating a distributed Slurm environment on local threads. GPU acceleration requires NVIDIA CUDA-Q bits installed.
                </p>
            </div>
        </div>
    );
}
