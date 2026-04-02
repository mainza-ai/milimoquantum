import React, { useState, useEffect } from 'react';
import { fetchHardwareProviders } from '../../services/api';

interface Backend {
    id: string;
    provider: string;
    name: string;
    qubits?: number;
    available: boolean;
    type: string;
    status?: string;
}

interface ProviderInfo {
    name: string;
    available: boolean;
    type: string;
    devices?: Backend[];
    targets?: Backend[];
}

export const HardwareBrowser: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [providers, setProviders] = useState<Record<string, ProviderInfo>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            setError(null);
            fetchHardwareProviders()
                .then((data) => {
                    setProviders(data.providers || {});
                })
                .catch((err) => {
                    setError('Failed to load hardware providers');
                    console.error(err);
                })
                .finally(() => setLoading(false));
        }
    }, [isOpen]);

    const allBackends: Backend[] = [];

    Object.entries(providers).forEach(([providerId, info]) => {
        if (info.devices) {
            info.devices.forEach((d) => {
                allBackends.push({
                    id: d.id || providerId,
                    provider: providerId.toUpperCase(),
                    name: d.name || d.id,
                    qubits: d.qubits,
                    available: d.available ?? info.available,
                    type: d.type || info.type,
                    status: d.available ? 'Online' : 'Offline',
                });
            });
        } else if (info.targets) {
            info.targets.forEach((t) => {
                allBackends.push({
                    id: t.id || providerId,
                    provider: providerId.toUpperCase(),
                    name: t.name || t.id,
                    qubits: t.qubits,
                    available: t.available ?? info.available,
                    type: t.type || info.type,
                    status: t.available ? 'Online' : 'Offline',
                });
            });
        } else {
            allBackends.push({
                id: providerId,
                provider: providerId.toUpperCase(),
                name: info.name,
                available: info.available,
                type: info.type,
                status: info.available ? 'Online' : 'Offline',
            });
        }
    });

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
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">
                                Multi-Cloud Target Discovery & Fidelity Metrics
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors cursor-pointer"
                    >
                        ✕
                    </button>
                </div>

                {/* Browser Grid */}
                <div className="flex-1 overflow-auto bg-[#05070a]">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-gray-400 text-sm">Loading hardware providers...</div>
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-red-400 text-sm">{error}</div>
                        </div>
                    ) : allBackends.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-gray-400 text-sm">No hardware providers available</div>
                        </div>
                    ) : (
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-[#080a0f] text-[10px] uppercase font-bold text-gray-500 tracking-wider">
                                <tr>
                                    <th className="px-6 py-3 border-b border-white/5">Target ID</th>
                                    <th className="px-6 py-3 border-b border-white/5">Cloud / Provider</th>
                                    <th className="px-6 py-3 border-b border-white/5">Type</th>
                                    <th className="px-6 py-3 border-b border-white/5">Qubits</th>
                                    <th className="px-6 py-3 border-b border-white/5">Status</th>
                                    <th className="px-6 py-3 border-b border-white/5 text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm text-gray-300">
                                {allBackends.map((be) => (
                                    <tr
                                        key={be.id}
                                        className="border-b border-white/2 hover:bg-white/2 transition-colors group"
                                    >
                                        <td className="px-6 py-5 font-mono text-xs text-white flex items-center gap-3">
                                            <div
                                                className={`w-2 h-2 rounded-full ${
                                                    be.available
                                                        ? 'bg-green-500'
                                                        : be.type === 'local'
                                                        ? 'bg-yellow-500'
                                                        : 'bg-red-500'
                                                }`}
                                            />
                                            {be.id}
                                        </td>
                                        <td className="px-6 py-5">
                                            <span
                                                className={`px-2 py-1 rounded text-[10px] font-bold ${
                                                    be.provider === 'IBM'
                                                        ? 'bg-blue-500/10 text-blue-400'
                                                        : be.provider === 'AWS' ||
                                                          be.provider === 'AMAZON_BRAKET'
                                                        ? 'bg-orange-500/10 text-orange-400'
                                                        : be.provider === 'AZURE'
                                                        ? 'bg-cyan-500/10 text-cyan-400'
                                                        : be.provider === 'AER'
                                                        ? 'bg-purple-500/10 text-purple-400'
                                                        : 'bg-gray-500/10 text-gray-400'
                                                }`}
                                            >
                                                {be.provider}
                                            </span>
                                        </td>
                                        <td className="px-6 py-5 text-gray-400">{be.type}</td>
                                        <td className="px-6 py-5 font-bold">
                                            {be.qubits !== undefined ? be.qubits : '—'}
                                        </td>
                                        <td className="px-6 py-5">
                                            <span
                                                className={`text-xs font-mono ${
                                                    be.available ? 'text-emerald-400' : 'text-red-400'
                                                }`}
                                            >
                                                {be.available ? 'Available' : 'Unavailable'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <button
                                                disabled={!be.available}
                                                className={`px-3 py-1 rounded text-xs font-bold transition-all cursor-pointer ${
                                                    be.available
                                                        ? 'bg-purple-500 text-black hover:bg-purple-400'
                                                        : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                                }`}
                                            >
                                                Select Target
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-purple-500/10 bg-[#0d1117] flex justify-between items-center text-[10px] font-bold uppercase text-gray-500">
                    <div className="flex gap-6">
                        <span>Aggregated Backends: {allBackends.length}</span>
                        <span className="text-emerald-500">Live Calibration Pulse: OK</span>
                    </div>
                    <button
                        onClick={() => {
                            setLoading(true);
                            fetchHardwareProviders()
                                .then((data) => setProviders(data.providers || {}))
                                .catch(() => setError('Failed to load hardware providers'))
                                .finally(() => setLoading(false));
                        }}
                        className="text-purple-400 hover:text-purple-300 transition-colors cursor-pointer"
                    >
                        Refresh Telemetry
                    </button>
                </div>
            </div>
        </div>
    );
};
