import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchCloudProviders, setCloudProvider, fetchCloudModels, searchCloudModels, fetchSettings, updateSettings } from '../../../services/api';

interface CloudModel {
    id: string;
    name: string;
    owner: string;
    description?: string;
    context_length?: number;
    pricing?: Record<string, number>;
}

interface Provider {
    id: string;
    name: string;
    description: string;
    configured: boolean;
    models: string[];
}

interface Settings {
    cloud_provider?: { provider: string; model: string };
    active_cloud_provider?: string;
    active_model?: string;
    cloud_provider_model?: string;
    openrouter_api_key?: string;
    nvidia_api_key?: string;
    [key: string]: any;
}

export function CloudProviderPanel() {
    const [providers, setProviders] = useState<Provider[]>([]);
    const [loading, setLoading] = useState(true);
    const [settings, setSettings] = useState<Settings | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
    const [apiKey, setApiKey] = useState('');

    // Model selection state
    const [models, setModels] = useState<CloudModel[]>([]);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [showModelDropdown, setShowModelDropdown] = useState(false);
    const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        Promise.all([
            fetchCloudProviders(),
            fetchSettings(),
        ]).then(([providersData, settingsData]) => {
            setProviders(providersData.providers || []);
            setSettings(settingsData);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowModelDropdown(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadModels = useCallback(async (providerId: string, query?: string) => {
        setModelsLoading(true);
        try {
            let data;
            if (query && query.length > 0) {
                data = await searchCloudModels(providerId, query);
            } else {
                data = await fetchCloudModels(providerId);
            }
            setModels(data.models || []);
        } catch (e) {
            console.error('Failed to load models:', e);
            setModels([]);
        } finally {
            setModelsLoading(false);
        }
    }, []);

    const handleProviderSelect = (providerId: string) => {
        setSelectedProvider(providerId);
        setSelectedModel('');
        setSearchQuery('');
        setModels([]);
        setShowModelDropdown(false);
        loadModels(providerId);
    };

    const handleSearchChange = (value: string) => {
        setSearchQuery(value);
        if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
        searchTimeoutRef.current = setTimeout(() => {
            if (selectedProvider) {
                loadModels(selectedProvider, value);
            }
        }, 300);
    };

    const handleModelSelect = (modelId: string) => {
        setSelectedModel(modelId);
        setShowModelDropdown(false);
    };

    const handleSaveProvider = async (providerId: string) => {
        try {
            const updateData: Record<string, unknown> = {};
            if (apiKey) {
                const keyField = `${providerId}_api_key`;
                updateData[keyField] = apiKey;
            }
            if (selectedModel) {
                updateData['cloud_provider_model'] = selectedModel;
            }
            if (Object.keys(updateData).length > 0) {
                await updateSettings(updateData);
            }
            await setCloudProvider(providerId, selectedModel || undefined);
            // Refresh settings
            const newSettings = await fetchSettings();
            setSettings(newSettings);
            setSelectedProvider(null);
            setApiKey('');
            setSelectedModel('');
        } catch (e) {
            console.error('Failed to save provider:', e);
            alert('Failed to save provider.');
        }
    };

    if (loading) return <div className="text-quantum-text-dim">Loading providers...</div>;

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium text-quantum-text">Cloud Hardware Providers</h3>
            
            {/* Current active provider display */}
            {(settings?.cloud_provider?.provider || settings?.active_cloud_provider) && (
                <div className="p-3 bg-quantum-cyan/10 border border-quantum-cyan/30 rounded-xl">
                    <p className="text-sm text-quantum-text">
                        Active: <span className="font-medium text-quantum-cyan">{settings.cloud_provider?.provider || settings.active_cloud_provider}</span>
                        {(settings.cloud_provider?.model || settings.cloud_provider_model) && (
                            <span className="text-quantum-text-dim"> — {settings.cloud_provider?.model || settings.cloud_provider_model}</span>
                        )}
                    </p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {providers.map(p => (
                    <div key={p.id} className="p-4 border border-quantum-border bg-quantum-surface rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-quantum-text">{p.name}</h4>
                            <span className={`text-xs px-2 py-1 rounded-full ${p.configured ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                {p.configured ? 'Configured' : 'Not configured'}
                            </span>
                        </div>
                        <p className="text-xs text-quantum-text-dim mb-4">{p.description}</p>
                        
                        {selectedProvider === p.id ? (
                            <div className="space-y-3">
                                {/* API Key input */}
                                <input 
                                    type="password" 
                                    placeholder="API Key" 
                                    className="w-full bg-[#0a0a0f] border border-quantum-border rounded px-3 py-2 text-sm text-quantum-text focus:border-quantum-cyan focus:outline-none"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                />
                                
                                {/* Model selector with search */}
                                <div className="relative" ref={dropdownRef}>
                                    <label className="text-xs text-quantum-text-dim mb-1 block">Select Model</label>
                                    <div className="relative">
                                        <input 
                                            type="text" 
                                            placeholder={modelsLoading ? "Loading models..." : "Search models..."}
                                            className="w-full bg-[#0a0a0f] border border-quantum-border rounded px-3 py-2 text-sm text-quantum-text focus:border-quantum-cyan focus:outline-none pr-8"
                                            value={searchQuery || selectedModel}
                                            onChange={(e) => {
                                                handleSearchChange(e.target.value);
                                                setShowModelDropdown(true);
                                            }}
                                            onFocus={() => setShowModelDropdown(true)}
                                        />
                                        {modelsLoading && (
                                            <div className="absolute right-2 top-2">
                                                <div className="w-4 h-4 border-2 border-quantum-cyan/30 border-t-quantum-cyan rounded-full animate-spin"></div>
                                            </div>
                                        )}
                                    </div>
                                    
                                    {showModelDropdown && (
                                        <div className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto bg-[#0a0a0f] border border-quantum-border rounded shadow-xl">
                                            {models.length === 0 && !modelsLoading ? (
                                                <div className="p-3 text-xs text-quantum-text-dim">No models found</div>
                                            ) : (
                                                models.map(m => (
                                                    <button
                                                        key={m.id}
                                                        className={`w-full text-left px-3 py-2 text-sm hover:bg-quantum-cyan/10 transition-colors ${selectedModel === m.id ? 'bg-quantum-cyan/20 text-quantum-cyan' : 'text-quantum-text'}`}
                                                        onClick={() => handleModelSelect(m.id)}
                                                    >
                                                        <div className="font-medium">{m.name || m.id}</div>
                                                        <div className="text-xs text-quantum-text-dim">
                                                            {m.owner}
                                                            {m.context_length && ` · ${m.context_length.toLocaleString()} ctx`}
                                                        </div>
                                                    </button>
                                                ))
                                            )}
                                        </div>
                                    )}
                                </div>
                                
                                <div className="flex gap-2">
                                    <button 
                                        className="flex-1 bg-quantum-cyan text-black px-3 py-1.5 rounded text-sm hover:opacity-90"
                                        onClick={() => handleSaveProvider(p.id)}
                                    >Save &amp; Activate</button>
                                    <button 
                                        className="flex-1 bg-quantum-surface border border-quantum-border px-3 py-1.5 rounded text-sm hover:bg-white/5"
                                        onClick={() => { setSelectedProvider(null); setApiKey(''); setSelectedModel(''); setSearchQuery(''); }}
                                    >Cancel</button>
                                </div>
                            </div>
                        ) : (
                            <button 
                                className="w-full bg-[#0a0a0f] border border-quantum-border hover:border-quantum-cyan/50 text-quantum-text px-3 py-2 rounded text-sm transition-colors"
                                onClick={() => handleProviderSelect(p.id)}
                            >
                                {p.configured ? 'Reconfigure' : 'Configure Integration'}
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
