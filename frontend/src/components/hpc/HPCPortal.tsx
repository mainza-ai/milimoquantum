import React, { useState } from 'react';

interface HPCJob {
    id: string;
    name: string;
    cluster: string;
    status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
    submitted_at: string;
}

export const HPCPortal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [jobs] = useState<HPCJob[]>([
        { id: 'job_442', name: 'VQE_H2O_Sweep', cluster: 'nvidia_dgx_h100', status: 'COMPLETED', submitted_at: '2026-02-27 10:05' },
        { id: 'job_445', name: 'QAOA_MaxCut_128Q', cluster: 'slurm_frontier', status: 'RUNNING', submitted_at: '2026-02-27 11:20' },
    ]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#0b0e14] border border-orange-500/20 rounded-2xl w-full max-w-4xl h-[70vh] flex flex-col overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="px-6 py-4 border-b border-orange-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-3">
                        <span className="text-xl">🏎️</span>
                        <div>
                            <h3 className="text-lg font-bold text-white">HPC & Accelerator Portal</h3>
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">CUDA-Q / SLURM / MPI Orchestration</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">✕</button>
                </div>

                {/* Dashboard Grid */}
                <div className="flex-1 overflow-auto p-6 bg-[#05070a]">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                        <div className="p-4 rounded-xl bg-[#0d1117] border border-orange-500/10">
                            <div className="text-[10px] text-gray-500 font-bold uppercase mb-1">Active Clusters</div>
                            <div className="text-2xl font-bold text-white">3</div>
                        </div>
                        <div className="p-4 rounded-xl bg-[#0d1117] border border-orange-500/10">
                            <div className="text-[10px] text-gray-500 font-bold uppercase mb-1">Compute Hours</div>
                            <div className="text-2xl font-bold text-orange-400">1,248.5</div>
                        </div>
                        <div className="p-4 rounded-xl bg-[#0d1117] border border-orange-500/10">
                            <div className="text-[10px] text-gray-500 font-bold uppercase mb-1">Queue Health</div>
                            <div className="text-2xl font-bold text-green-500">Nominal</div>
                        </div>
                    </div>

                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Active slurm queue</h4>
                    <div className="space-y-2">
                        {jobs.map(job => (
                            <div key={job.id} className="p-4 rounded-xl bg-[#0d1117] border border-white/5 flex items-center justify-between hover:border-orange-500/20 transition-all">
                                <div className="flex items-center gap-4">
                                    <div className={`w-2 h-2 rounded-full ${job.status === 'COMPLETED' ? 'bg-green-500' :
                                            job.status === 'RUNNING' ? 'bg-orange-500 animate-pulse' : 'bg-gray-500'
                                        }`} />
                                    <div>
                                        <div className="text-sm font-bold text-white">{job.name}</div>
                                        <div className="text-[10px] text-gray-500 font-mono">{job.id} • {job.cluster}</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-[10px] text-gray-400">{job.submitted_at}</div>
                                    <div className="text-xs font-bold text-orange-400">{job.status}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <button className="mt-6 w-full py-3 rounded-xl border-2 border-dashed border-orange-500/20 text-orange-500/60 hover:border-orange-500/40 hover:text-orange-400 transition-all text-sm font-bold">
                        + New HPC Job Submission
                    </button>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-orange-500/10 bg-[#0d1117] flex justify-between items-center">
                    <span className="text-[10px] text-gray-500 font-bold uppercase">NVIDIA H100 GPU Pool: 14/16 Available</span>
                    <button className="text-xs font-bold text-orange-400 hover:text-orange-300 transition-colors">
                        View Slurm Config
                    </button>
                </div>
            </div>
        </div>
    );
};
