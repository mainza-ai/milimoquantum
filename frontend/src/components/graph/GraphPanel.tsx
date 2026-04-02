import React, { useState, useEffect } from 'react';
import { fetchGraphStatus, fetchGraphStats, fetchGraphRelated } from '../../services/api';

export const GraphPanel: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [stats, setStats] = useState<any>(null);
    const [query, setQuery] = useState('');
    const [related, setRelated] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchGraphStatus().then(setStatus).catch(() => {});
        fetchGraphStats().then(setStats).catch(() => {});
    }, []);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        try {
            const data = await fetchGraphRelated(query);
            setRelated(data.nodes || []);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 h-full overflow-auto">
            <div className="flex items-center gap-3 mb-6">
                <span className="text-2xl">🕸️</span>
                <div>
                    <h2 className="text-lg font-bold text-white">Graph Intelligence</h2>
                    <p className="text-xs text-gray-500">Knowledge Graph & Agent Memory</p>
                </div>
            </div>

            {status && (
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-black/20 rounded-lg p-4 border border-white/5">
                        <div className="text-[10px] text-gray-500 uppercase mb-1">Status</div>
                        <div className={`text-sm font-medium ${status.connected ? 'text-green-400' : 'text-red-400'}`}>
                            {status.connected ? 'Connected' : 'Disconnected'}
                        </div>
                        {status.backend && (
                            <div className="text-[10px] text-gray-500 mt-1">{status.backend}</div>
                        )}
                    </div>
                    {stats && (
                        <div className="bg-black/20 rounded-lg p-4 border border-white/5">
                            <div className="text-[10px] text-gray-500 uppercase mb-1">Nodes</div>
                            <div className="text-sm font-medium text-cyan-400">
                                {stats.node_count !== undefined ? stats.node_count.toLocaleString() : '—'}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="mb-6">
                <label className="text-[10px] text-gray-500 uppercase mb-2 block">Semantic Search</label>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search concepts, circuits, molecules..."
                        className="flex-1 bg-white/[0.02] border border-white/[0.06] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/30"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-lg text-sm font-medium hover:bg-cyan-500/20 transition-all disabled:opacity-50 cursor-pointer"
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </div>

            {related.length > 0 && (
                <div>
                    <div className="text-[10px] text-gray-500 uppercase mb-2">Related Nodes</div>
                    <div className="space-y-2">
                        {related.map((node, i) => (
                            <div
                                key={i}
                                className="bg-black/20 rounded-lg p-3 border border-white/5 flex items-center gap-3"
                            >
                                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-lg">
                                    {node.type === 'Concept' ? '💡' : node.type === 'Circuit' ? '⚛️' : node.type === 'Molecule' ? '🧬' : '📦'}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-white truncate">{node.name || node.id}</div>
                                    <div className="text-[10px] text-gray-500">{node.type}</div>
                                </div>
                                {node.score !== undefined && (
                                    <div className="text-xs text-cyan-400 font-mono">{(node.score * 100).toFixed(0)}%</div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {stats && stats.node_types && (
                <div className="mt-6">
                    <div className="text-[10px] text-gray-500 uppercase mb-2">Node Types</div>
                    <div className="flex flex-wrap gap-2">
                        {Object.entries(stats.node_types).map(([type, count]: [string, any]) => (
                            <div
                                key={type}
                                className="px-3 py-1.5 bg-white/[0.02] border border-white/[0.06] rounded-lg text-xs text-gray-400"
                            >
                                {type}: {count}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
