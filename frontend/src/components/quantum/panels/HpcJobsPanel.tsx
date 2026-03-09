import { useState, useEffect } from 'react';
import { checkHpcStatus } from '../../../services/api';

export function HpcJobsPanel() {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkHpcStatus().then(data => {
            setStatus(data);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    if (loading) return <div>Checking HPC router...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-quantum-text">HPC Job Queue</h3>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${status?.healthy ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm text-quantum-text-dim">Router {status?.healthy ? 'Online' : 'Offline'}</span>
                </div>
            </div>

            <div className="bg-[#0a0a0f] border border-quantum-border rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-[#18181f] text-quantum-text-dim border-b border-quantum-border">
                        <tr>
                            <th className="px-4 py-3 font-medium">Job ID</th>
                            <th className="px-4 py-3 font-medium">Algorithm</th>
                            <th className="px-4 py-3 font-medium">Status</th>
                            <th className="px-4 py-3 font-medium">Submitted</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-quantum-border/50 text-quantum-text">
                        {status?.active_jobs?.length > 0 ? (
                            status.active_jobs.map((job: any) => (
                                <tr key={job.id} className="hover:bg-white/[0.02]">
                                    <td className="px-4 py-3 font-mono text-xs">{job.id.substring(0,8)}</td>
                                    <td className="px-4 py-3">{job.name}</td>
                                    <td className="px-4 py-3">
                                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs">
                                            {job.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-quantum-text-dim text-xs">Just now</td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={4} className="px-4 py-8 text-center text-quantum-text-dim">
                                    No active jobs in the queue.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="p-4 bg-quantum-cyan/5 border border-quantum-cyan/20 rounded-xl">
                <h4 className="text-sm font-medium text-quantum-cyan mb-2">Notice</h4>
                <p className="text-xs text-quantum-text-dim leading-relaxed">
                    HPC jobs are routed via Celery to the nearest available worker based on your configured Cloud Providers. Heavy simulations (N{'>'}24) will automatically be queued here.
                </p>
            </div>
        </div>
    );
}
