import { useState, useEffect } from 'react';
import { fetchCloudProviders, setCloudProvider } from '../../../services/api';

export function CloudProviderPanel() {
    const [providers, setProviders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState<string | null>(null);
    const [apiKey, setApiKey] = useState('');

    useEffect(() => {
        fetchCloudProviders().then(data => {
            setProviders(data.providers || []);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    const handleSave = async (providerId: string) => {
        try {
            await setCloudProvider(providerId, undefined, apiKey);
            alert('Provider credentials saved successfully.');
            setApiKey('');
        } catch (e) {
            alert('Failed to save provider.');
        }
    };

    if (loading) return <div>Loading providers...</div>;

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium text-quantum-text">Cloud Hardware Providers</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {providers.map(p => (
                    <div key={p.id} className="p-4 border border-quantum-border bg-quantum-surface rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-quantum-text">{p.name}</h4>
                            <span className={`text-xs px-2 py-1 rounded-full ${p.connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                {p.connected ? 'Connected' : 'Disconnected'}
                            </span>
                        </div>
                        <p className="text-xs text-quantum-text-dim mb-4">{p.description}</p>
                        
                        {selected === p.id ? (
                            <div className="space-y-3">
                                <input 
                                    type="password" 
                                    placeholder="API Key / Token" 
                                    className="w-full bg-[#0a0a0f] border border-quantum-border rounded px-3 py-2 text-sm text-quantum-text focus:border-quantum-cyan focus:outline-none"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                />
                                <div className="flex gap-2">
                                    <button 
                                        className="flex-1 bg-quantum-cyan text-black px-3 py-1.5 rounded text-sm hover:opacity-90"
                                        onClick={() => handleSave(p.id)}
                                    >Save</button>
                                    <button 
                                        className="flex-1 bg-quantum-surface border border-quantum-border px-3 py-1.5 rounded text-sm hover:bg-white/5"
                                        onClick={() => { setSelected(null); setApiKey(''); }}
                                    >Cancel</button>
                                </div>
                            </div>
                        ) : (
                            <button 
                                className="w-full bg-[#0a0a0f] border border-quantum-border hover:border-quantum-cyan/50 text-quantum-text px-3 py-2 rounded text-sm transition-colors"
                                onClick={() => setSelected(p.id)}
                            >
                                Configure Integration
                            </button>
                        )}
                    </div>
                ))}
            </div>
            {providers.length === 0 && (
                <div className="text-center py-8 text-quantum-text-dim border border-dashed border-quantum-border rounded-xl">
                    No cloud providers available. Check backend configuration.
                </div>
            )}
        </div>
    );
}
