/* Milimo Quantum — Cloud AI Settings + Local Settings Panel */
import { useState, useEffect } from 'react';
import { fetchSettings, fetchModels, updateSettings, fetchCloudProviders, setCloudProvider } from '../../services/api';

interface CloudProvider {
    id: string;
    name: string;
    models: string[];
    configured: boolean;
}

interface SettingsPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
    const [model, setModel] = useState('');
    const [models, setModels] = useState<string[]>([]);
    const [shots, setShots] = useState(1024);
    const [ollamaUrl, setOllamaUrl] = useState('');
    const [platform, setPlatform] = useState<Record<string, string>>({});
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Cloud AI state
    const [providers, setProviders] = useState<CloudProvider[]>([]);
    const [activeProvider, setActiveProvider] = useState('ollama');
    const [cloudModel, setCloudModel] = useState('');
    const [cloudSaving, setCloudSaving] = useState(false);
    const [cloudSaved, setCloudSaved] = useState(false);
    const [activeTab, setActiveTab] = useState<'local' | 'cloud'>('local');

    useEffect(() => {
        if (!isOpen) return;
        fetchSettings().then((data) => {
            setModel(data.ollama_model || '');
            setShots(data.default_shots || 1024);
            setOllamaUrl(data.ollama_url || '');
            setPlatform(data.platform || {});
            if (data.cloud_provider?.provider && data.cloud_provider.provider !== 'ollama') {
                setActiveProvider(data.cloud_provider.provider);
                setCloudModel(data.cloud_provider.model || '');
            }
        }).catch(() => { });

        fetchModels().then((data) => {
            setModels(data.models || []);
        }).catch(() => { });

        fetchCloudProviders().then((data) => {
            setProviders(data.providers || []);
        }).catch(() => { });
    }, [isOpen]);

    const handleSave = async () => {
        setSaving(true);
        await updateSettings({ ollama_model: model, default_shots: shots, ollama_url: ollamaUrl });
        setSaving(false);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleCloudSave = async () => {
        setCloudSaving(true);
        await setCloudProvider(activeProvider, cloudModel || undefined);
        setCloudSaving(false);
        setCloudSaved(true);
        setTimeout(() => setCloudSaved(false), 2000);
    };

    if (!isOpen) return null;

    const selectedCloudProvider = providers.find(p => p.id === activeProvider);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div
                className="w-full max-w-lg rounded-2xl border border-white/[0.08]
                    bg-gradient-to-b from-[#0c0c14] to-[#060610]
                    shadow-2xl shadow-black/50 overflow-hidden max-h-[85vh] flex flex-col"
                style={{ animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] shrink-0">
                    <h2 className="text-lg font-semibold text-white tracking-tight">Settings</h2>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-lg
                            hover:bg-white/[0.06] text-[#636370] hover:text-white transition-all cursor-pointer"
                    >✕</button>
                </div>

                {/* Tab bar */}
                <div className="flex px-6 pt-3 gap-1 shrink-0">
                    <button
                        onClick={() => setActiveTab('local')}
                        className={`px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer
                            ${activeTab === 'local'
                                ? 'bg-white/[0.08] text-white border border-white/[0.1]'
                                : 'text-[#636370] hover:text-white hover:bg-white/[0.04]'
                            }`}
                    >🖥️ Local (Ollama)</button>
                    <button
                        onClick={() => setActiveTab('cloud')}
                        className={`px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer
                            ${activeTab === 'cloud'
                                ? 'bg-white/[0.08] text-white border border-white/[0.1]'
                                : 'text-[#636370] hover:text-white hover:bg-white/[0.04]'
                            }`}
                    >☁️ Cloud AI</button>
                </div>

                {/* Body */}
                <div className="px-6 py-5 space-y-5 overflow-y-auto flex-1">
                    {activeTab === 'local' ? (
                        <>
                            {/* Model Selector */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">LLM Model</label>
                                {models.length > 0 ? (
                                    <select
                                        value={model}
                                        onChange={(e) => setModel(e.target.value)}
                                        className="w-full px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                            text-white text-sm focus:outline-none focus:border-[#3ecfef]/40
                                            transition-colors appearance-none cursor-pointer"
                                    >
                                        {models.map((m) => (
                                            <option key={m} value={m} className="bg-[#0c0c14]">{m}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <input
                                        value={model}
                                        onChange={(e) => setModel(e.target.value)}
                                        placeholder="llama3.2:3b-instruct-fp16"
                                        className="w-full px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                            text-white text-sm focus:outline-none focus:border-[#3ecfef]/40 transition-colors"
                                    />
                                )}
                            </div>

                            {/* Default Shots */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">
                                    Default Shots <span className="text-[#636370]">({shots})</span>
                                </label>
                                <input
                                    type="range" min="100" max="8192" step="100"
                                    value={shots}
                                    onChange={(e) => setShots(Number(e.target.value))}
                                    className="w-full accent-[#3ecfef]"
                                />
                                <div className="flex justify-between text-xs text-[#636370] mt-1">
                                    <span>100</span><span>8192</span>
                                </div>
                            </div>

                            {/* Ollama URL */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">Ollama URL</label>
                                <input
                                    value={ollamaUrl}
                                    onChange={(e) => setOllamaUrl(e.target.value)}
                                    placeholder="http://localhost:11434"
                                    className="w-full px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                        text-white text-sm font-mono focus:outline-none focus:border-[#3ecfef]/40 transition-colors"
                                />
                            </div>

                            {/* Platform Info */}
                            {Object.keys(platform).length > 0 && (
                                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                                    <h3 className="text-xs font-medium text-[#636370] mb-2 uppercase tracking-wider">Platform</h3>
                                    <div className="grid grid-cols-2 gap-1.5 text-xs">
                                        {Object.entries(platform).map(([k, v]) => (
                                            <div key={k}>
                                                <span className="text-[#636370]">{k}: </span>
                                                <span className="text-[#a1a1aa]">{String(v)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <>
                            {/* Cloud Provider Selector */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-2">AI Provider</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => { setActiveProvider('ollama'); setCloudModel(''); }}
                                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer
                                            ${activeProvider === 'ollama'
                                                ? 'border-[#3ecfef]/40 bg-[#3ecfef]/5'
                                                : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]'}`}
                                    >
                                        <div className="text-sm font-medium text-white">🖥️ Ollama</div>
                                        <div className="text-[10px] text-[#636370] mt-0.5">Local, free, private</div>
                                        <div className="text-[10px] text-green-400 mt-1">● Active</div>
                                    </button>
                                    {providers.map(p => (
                                        <button
                                            key={p.id}
                                            onClick={() => { setActiveProvider(p.id); setCloudModel(p.models[0] || ''); }}
                                            className={`p-3 rounded-xl border text-left transition-all cursor-pointer
                                                ${activeProvider === p.id
                                                    ? 'border-[#3ecfef]/40 bg-[#3ecfef]/5'
                                                    : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]'}`}
                                        >
                                            <div className="text-sm font-medium text-white">
                                                {p.id === 'anthropic' ? '🟠' : p.id === 'openai' ? '🟢' : '🔵'} {p.name}
                                            </div>
                                            <div className="text-[10px] text-[#636370] mt-0.5">
                                                {p.models.length} models
                                            </div>
                                            <div className={`text-[10px] mt-1 ${p.configured ? 'text-green-400' : 'text-[#636370]'}`}>
                                                {p.configured ? '● Key set' : '○ Not configured'}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Cloud Model Selector */}
                            {activeProvider !== 'ollama' && selectedCloudProvider && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">Model</label>
                                        <select
                                            value={cloudModel}
                                            onChange={(e) => setCloudModel(e.target.value)}
                                            className="w-full px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                                text-white text-sm focus:outline-none focus:border-[#3ecfef]/40
                                                transition-colors appearance-none cursor-pointer"
                                        >
                                            {selectedCloudProvider.models.map(m => (
                                                <option key={m} value={m} className="bg-[#0c0c14]">{m}</option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* API Key input */}
                                    <div>
                                        <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">API Key</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="password"
                                                placeholder={`Enter ${activeProvider === 'anthropic' ? 'ANTHROPIC_API_KEY' :
                                                    activeProvider === 'openai' ? 'OPENAI_API_KEY' : 'GOOGLE_API_KEY'}`}
                                                className="flex-1 px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                                    text-white text-sm font-mono focus:outline-none focus:border-[#3ecfef]/40 transition-colors"
                                                id="cloud-api-key-input"
                                            />
                                            <button
                                                onClick={async () => {
                                                    const input = document.getElementById('cloud-api-key-input') as HTMLInputElement;
                                                    if (input?.value) {
                                                        const keyMap: Record<string, string> = {
                                                            anthropic: 'anthropic_api_key',
                                                            openai: 'openai_api_key',
                                                            gemini: 'gemini_api_key',
                                                        };
                                                        await updateSettings({ [keyMap[activeProvider]]: input.value });
                                                        input.value = '';
                                                        // Refresh provider list to update configured status
                                                        fetchCloudProviders().then((data) => setProviders(data.providers || []));
                                                    }
                                                }}
                                                className="px-3 py-2 rounded-xl text-xs font-medium cursor-pointer
                                                    bg-white/[0.06] border border-white/[0.08] text-[#3ecfef]
                                                    hover:bg-[#3ecfef]/10 transition-all"
                                            >Set</button>
                                        </div>
                                        {selectedCloudProvider.configured ? (
                                            <p className="text-[10px] text-green-400 mt-1.5">✓ API key configured</p>
                                        ) : (
                                            <p className="text-[10px] text-[#636370] mt-1.5">
                                                Or set <code className="text-amber-300 bg-white/5 px-1 rounded text-[10px]">
                                                    {activeProvider === 'anthropic' ? 'ANTHROPIC_API_KEY' :
                                                        activeProvider === 'openai' ? 'OPENAI_API_KEY' : 'GOOGLE_API_KEY'}
                                                </code> env var before starting the backend.
                                            </p>
                                        )}
                                    </div>
                                </>
                            )}

                            {activeProvider === 'ollama' && (
                                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] text-center">
                                    <div className="text-2xl mb-2">🖥️</div>
                                    <p className="text-sm text-[#a1a1aa]">Using local Ollama</p>
                                    <p className="text-xs text-[#636370] mt-1">
                                        Model: <span className="text-[#3ecfef] font-mono">{model || 'default'}</span>
                                    </p>
                                    <p className="text-[10px] text-[#636370] mt-2">
                                        Switch to the Local tab to change Ollama settings.
                                    </p>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.06] shrink-0">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-xl text-sm text-[#a1a1aa]
                            hover:bg-white/[0.04] transition-colors cursor-pointer"
                    >Cancel</button>
                    <button
                        onClick={activeTab === 'local' ? handleSave : handleCloudSave}
                        disabled={saving || cloudSaving}
                        className="px-5 py-2 rounded-xl text-sm font-medium cursor-pointer
                            bg-gradient-to-r from-[#3ecfef]/20 to-[#5bb8d4]/20
                            border border-[#3ecfef]/20 text-[#3ecfef]
                            hover:from-[#3ecfef]/30 hover:to-[#5bb8d4]/30
                            transition-all active:scale-[0.98]"
                    >{(activeTab === 'local' ? saved : cloudSaved) ? '✓ Saved' : (saving || cloudSaving) ? 'Saving...' : 'Save'}</button>
                </div>
            </div>
        </div>
    );
}
