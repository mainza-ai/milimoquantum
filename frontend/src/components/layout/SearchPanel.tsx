/* Milimo Quantum — Semantic Search Panel */
import { useState, useCallback } from 'react';

interface SearchResult {
    id: string;
    score: number;
    type: string;
    title: string;
    preview: string;
}

export function SearchPanel({ isOpen, onClose, onLoadConversation }: { isOpen: boolean; onClose: () => void; onLoadConversation?: (id: string) => void }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = useCallback(async () => {
        if (!query.trim()) return;
        setLoading(true);
        setSearched(true);
        try {
            const res = await fetch(`/api/search/?q=${encodeURIComponent(query)}&n=10`);
            const data = await res.json();
            setResults(data.results || []);
        } catch {
            setResults([]);
        } finally {
            setLoading(false);
        }
    }, [query]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
        w-full max-w-2xl max-h-[80vh] overflow-hidden mx-4 flex flex-col">
                {/* Header */}
                <div className="border-b border-cyan-500/10 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🔍</span>
                        <h2 className="text-lg font-semibold text-white">Semantic Search</h2>
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
              flex items-center justify-center text-gray-400 hover:text-white
              transition-all cursor-pointer">✕</button>
                </div>

                {/* Search Input */}
                <div className="px-6 py-4 border-b border-white/5">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()}
                            placeholder="Search experiments, conversations by meaning..."
                            className="flex-1 bg-white/[0.04] border border-white/10 rounded-xl px-4 py-2.5
                text-sm text-white placeholder-gray-500
                focus:outline-none focus:border-cyan-500/40 transition-colors"
                            autoFocus
                        />
                        <button
                            onClick={handleSearch}
                            disabled={loading || !query.trim()}
                            className="px-5 py-2.5 rounded-xl text-sm font-medium
                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                hover:bg-cyan-500/20 hover:border-cyan-500/40
                disabled:opacity-40 disabled:cursor-not-allowed
                transition-all cursor-pointer"
                        >
                            {loading ? '...' : 'Search'}
                        </button>
                    </div>
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {loading ? (
                        <div className="flex items-center justify-center py-12 text-gray-400">
                            <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                            Searching...
                        </div>
                    ) : results.length > 0 ? (
                        <div className="space-y-3">
                            {results.map((result, idx) => (
                                <div key={result.id}
                                    onClick={() => {
                                        if (result.type === 'conversation' && onLoadConversation) {
                                            onLoadConversation(result.id);
                                            onClose();
                                        }
                                    }}
                                    className={`bg-white/[0.02] border border-white/[0.06] rounded-xl p-4
                                        hover:border-cyan-500/20 transition-all
                                        ${result.type === 'conversation' ? 'cursor-pointer' : ''}`}>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                            {result.type}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            Score: {(result.score * 100).toFixed(0)}%
                                        </span>
                                        <span className="text-xs text-gray-600 ml-auto">#{idx + 1}</span>
                                    </div>
                                    {result.title && (
                                        <div className="text-sm font-medium text-gray-300 mb-1">{result.title}</div>
                                    )}
                                    <div className="text-xs text-gray-500 leading-relaxed">{result.preview}</div>
                                </div>
                            ))}
                        </div>
                    ) : searched ? (
                        <div className="text-center py-12 text-gray-500">
                            <div className="text-3xl mb-3">🔍</div>
                            <p className="text-sm">No results found. Try a different query.</p>
                        </div>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <div className="text-3xl mb-3">✨</div>
                            <p className="text-sm">Search across your experiments and conversations</p>
                            <p className="text-xs mt-1 text-gray-600">Uses AI embeddings for semantic matching</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
