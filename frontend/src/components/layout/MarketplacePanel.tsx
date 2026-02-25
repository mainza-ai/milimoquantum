/* Milimo Quantum — Quantum App Marketplace */
import { useState, useEffect } from 'react';
import { fetchMarketplacePlugins, installPlugin } from '../../services/api';

interface Plugin {
    id: string;
    name: string;
    author: string;
    description: string;
    version: string;
    downloads: number;
    rating: number;
    tags: string[];
    installed?: boolean;
}

export function MarketplacePanel({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const [plugins, setPlugins] = useState<Plugin[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        fetchMarketplacePlugins()
            .then(res => setPlugins(res.plugins || []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [isOpen]);

    const handleInstall = async (id: string) => {
        try {
            await installPlugin(id);
            // Optimistic update
            setPlugins(plugins.map(p => p.id === id ? { ...p, installed: true } : p));
        } catch {
            // Handle error
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
        w-full max-w-4xl max-h-[85vh] overflow-hidden mx-4 flex flex-col">
                {/* Header */}
                <div className="border-b border-cyan-500/10 px-6 py-4 flex items-center justify-between bg-[#0d1117] z-10 relative">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🛍️</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Quantum App Marketplace</h2>
                            <p className="text-xs text-gray-400 mt-0.5">Discover community agents, optimizers, and plugins</p>
                        </div>
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
              flex items-center justify-center text-gray-400 hover:text-white
              transition-all cursor-pointer">✕</button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-20 text-gray-400">
                            <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                            Loading marketplace...
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {plugins.map(plugin => (
                                <div key={plugin.id}
                                    className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5
                    hover:border-cyan-500/30 transition-all flex flex-col h-full relative group">

                                    {/* Decorative glow */}
                                    <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 via-transparent to-purple-500/0 
                    group-hover:from-cyan-500/5 group-hover:to-purple-500/5 rounded-xl transition-all duration-500 pointer-events-none" />

                                    <div className="flex justify-between items-start mb-3 relative z-10">
                                        <div>
                                            <h3 className="text-base font-semibold text-white group-hover:text-cyan-400 transition-colors">
                                                {plugin.name}
                                            </h3>
                                            <div className="text-xs text-cyan-500/70 mt-0.5 font-mono">
                                                @{plugin.author} · v{plugin.version}
                                            </div>
                                        </div>
                                        {plugin.installed ? (
                                            <span className="px-3 py-1 bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg text-xs font-medium">
                                                Installed ✅
                                            </span>
                                        ) : (
                                            <button
                                                onClick={() => handleInstall(plugin.id)}
                                                className="px-4 py-1.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg text-xs font-medium
                          hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all cursor-pointer"
                                            >
                                                Install
                                            </button>
                                        )}
                                    </div>

                                    <p className="text-sm text-gray-400 flex-1 mb-4 leading-relaxed relative z-10">
                                        {plugin.description}
                                    </p>

                                    <div className="flex flex-wrap items-center gap-3 relative z-10">
                                        <div className="flex items-center gap-1.5 text-xs text-gray-500 pr-3 border-r border-white/5">
                                            <span className="text-yellow-500/80">★</span> {plugin.rating}
                                        </div>
                                        <div className="flex items-center gap-1.5 text-xs text-gray-500 pr-3 border-r border-white/5">
                                            <span className="text-blue-400/80">↓</span> {plugin.downloads.toLocaleString()}
                                        </div>
                                        <div className="flex gap-1.5">
                                            {plugin.tags.slice(0, 2).map(tag => (
                                                <span key={tag} className="px-2 py-0.5 bg-white/5 text-gray-400 rounded text-[10px] uppercase tracking-wider">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
