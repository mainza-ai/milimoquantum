import React, { useState } from 'react';

interface AuditLog {
    id: string;
    timestamp: string;
    user: string;
    action: string;
    resource: string;
    status: 'Success' | 'Failed' | 'Warning';
}

export const AuditDashboard: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [logs] = useState<AuditLog[]>([
        { id: '1', timestamp: '2026-02-27 14:22:01', user: 'mck', action: 'circuit_execute', resource: 'ibm_kyiv_v1', status: 'Success' },
        { id: '2', timestamp: '2026-02-27 14:15:33', user: 'system', action: 'graph_reindex', resource: 'agent_memory', status: 'Success' },
        { id: '3', timestamp: '2026-02-27 13:58:12', user: 'mck', action: 'auth_login', resource: 'keycloak_sso', status: 'Success' },
        { id: '4', timestamp: '2026-02-27 12:44:05', user: 'guest_user', action: 'unauthorized_access', resource: 'hpc_cluster', status: 'Failed' },
    ]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#0b0e14] border border-red-500/20 rounded-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="px-6 py-4 border-b border-red-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-3">
                        <span className="text-xl">🛡️</span>
                        <div>
                            <h3 className="text-lg font-bold text-white">Security & Audit Dashboard</h3>
                            <p className="text-[10px] text-gray-500">Real-time compliance monitoring and RBAC validation</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">✕</button>
                </div>

                {/* Filters */}
                <div className="px-6 py-3 border-b border-white/5 bg-[#080a0f] flex gap-4">
                    <select className="bg-[#0d1117] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-400 outline-none focus:border-red-500/40">
                        <option>All Users</option>
                        <option>MCK</option>
                        <option>System</option>
                    </select>
                    <select className="bg-[#0d1117] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-400 outline-none focus:border-red-500/40">
                        <option>All Actions</option>
                        <option>Circuit Execution</option>
                        <option>Auth Events</option>
                    </select>
                </div>

                {/* Table */}
                <div className="flex-1 overflow-auto bg-[#05070a]">
                    <table className="w-full text-left border-collapse">
                        <thead className="sticky top-0 bg-[#080a0f] text-[10px] uppercase font-bold text-gray-500 tracking-wider">
                            <tr>
                                <th className="px-6 py-3 border-b border-white/5">Timestamp</th>
                                <th className="px-6 py-3 border-b border-white/5">Identity</th>
                                <th className="px-6 py-3 border-b border-white/5">Action</th>
                                <th className="px-6 py-3 border-b border-white/5">Resource</th>
                                <th className="px-6 py-3 border-b border-white/5">Security Status</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm text-gray-300">
                            {logs.map((log) => (
                                <tr key={log.id} className="border-b border-white/2 hover:bg-white/2 transition-colors group">
                                    <td className="px-6 py-4 font-mono text-xs text-gray-500">{log.timestamp}</td>
                                    <td className="px-6 py-4">
                                        <span className="px-2 py-1 rounded bg-white/5 border border-white/10 text-xs font-medium">
                                            {log.user}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-medium">{log.action}</td>
                                    <td className="px-6 py-4 text-xs text-gray-400">{log.resource}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold ${log.status === 'Success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                                log.status === 'Failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse' :
                                                    'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                            }`}>
                                            {log.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Footer Summary */}
                <div className="px-6 py-4 border-t border-white/5 bg-[#0d1117] flex justify-between items-center">
                    <div className="flex gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                            <span className="text-[10px] text-gray-500 uppercase font-bold">Node Integrity: 100%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            <span className="text-[10px] text-gray-500 uppercase font-bold">Auth Fabric: Healthy</span>
                        </div>
                    </div>
                    <button className="text-xs font-bold text-red-400 hover:text-red-300 transition-colors">
                        Export Audit Trail (JSON)
                    </button>
                </div>
            </div>
        </div>
    );
};
