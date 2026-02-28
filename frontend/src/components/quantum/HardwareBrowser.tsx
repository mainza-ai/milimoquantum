import React, { useState } from 'react';

interface Backend {
    id: string;
    provider: 'IBM' | 'AWS' | 'Azure' | 'IonQ';
    qubits: number;
    fidelity: string;
    queue: string;
    status: 'Online' | 'Maintenance' | 'Offline';
}

export const HardwareBrowser: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [backends] = useState<Backend[]>([
        { id: 'ibm_kyiv', provider: 'IBM', qubits: 127, fidelity: '99.8%', queue: '2h 15m', status: 'Online' },
        { id: 'aws_ionq_aria', provider: 'AWS', qubits: 25, fidelity: '99.95%', queue: '15m', status: 'Online' },
        { id: 'azure_quantinuum_h1', provider: 'Azure', qubits: 20, fidelity: '99.97%', queue: '4h 30m', status: 'Online' },
        { id: 'rigetti_aspen_m3', provider: 'AWS', qubits: 80, fidelity: '98.2%', queue: 'Instant', status: 'Maintenance' },
    ]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#0b0e14] border border-purple-500/20 rounded-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="px-6 py-4 border-b border-purple-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-3">
                        <span className="text-xl">🛰️</span>
                        <div>
                            <h3 className="text-lg font-bold text-white">Quantum Hardware Browser</h3>
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Multi-Cloud Target Discovery & Fidelity Metrics</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">✕</button>
                </div>

                {/* Browser Grid */}
                <div className="flex-1 overflow-auto bg-[#05070a]">
                    <table className="w-full text-left border-collapse">
                        <thead className="sticky top-0 bg-[#080a0f] text-[10px] uppercase font-bold text-gray-500 tracking-wider">
                            <tr>
                                <th className="px-6 py-3 border-b border-white/5">Target ID</th>
                                <th className="px-6 py-3 border-b border-white/5">Cloud / Provider</th>
                                <th className="px-6 py-3 border-b border-white/5">Qubits</th>
                                <th className="px-6 py-3 border-b border-white/5">Gate Fidelity</th>
                                <th className="px-6 py-3 border-b border-white/5">Queue Time</th>
                                <th className="px-6 py-3 border-b border-white/5 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm text-gray-300">
                            {backends.map((be) => (
                                <tr key={be.id} className="border-b border-white/2 hover:bg-white/2 transition-colors group">
                                    <td className="px-6 py-5 font-mono text-xs text-white flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${be.status === 'Online' ? 'bg-green-500' : be.status === 'Maintenance' ? 'bg-yellow-500' : 'bg-red-500'}`} />
                                        {be.id}
                                    </td>
                                    <td className="px-6 py-5">
                                        <span className={`px-2 py-1 rounded text-[10px] font-bold ${be.provider === 'IBM' ? 'bg-blue-500/10 text-blue-400' :
                                                be.provider === 'AWS' ? 'bg-orange-500/10 text-orange-400' :
                                                    'bg-cyan-500/10 text-cyan-400'
                                            }`}>
                                            {be.provider}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5 font-bold">{be.qubits}</td>
                                    <td className="px-6 py-5 text-emerald-400 font-mono">{be.fidelity}</td>
                                    <td className="px-6 py-5 text-gray-400">{be.queue}</td>
                                    <td className="px-6 py-5 text-right">
                                        <button className="px-3 py-1 rounded bg-purple-500 text-black text-xs font-bold hover:bg-purple-400 transition-all">
                                            Select Target
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-purple-500/10 bg-[#0d1117] flex justify-between items-center text-[10px] font-bold uppercase text-gray-500">
                    <div className="flex gap-6">
                        <span>Aggregated Backends: 14</span>
                        <span className="text-emerald-500">Live Calibration Pulse: OK</span>
                    </div>
                    <button className="text-purple-400 hover:text-purple-300 transition-colors">Refresh Telemetry</button>
                </div>
            </div>
        </div>
    );
};
