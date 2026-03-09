import { useState, useEffect } from 'react';
import { fetchSettings, fetchModels, updateSettings, fetchCloudProviders, setCloudProvider, fetchMLXModels, searchMLXModels, pullMLXModel } from '../../services/api';
import { CloudProviderPanel } from '../quantum/panels/CloudProviderPanel';

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
    const [savedProvider, setSavedProvider] = useState<string>('ollama');
    const [activeTab, setActiveTab] = useState<'local' | 'cloud' | 'mlx'>('local');

    // MLX state
    const [mlxModels, setMlxModels] = useState<string[]>([]);
    const [activeMlxModel, setActiveMlxModel] = useState<string>('');
    const [mlxSearchQuery, setMlxSearchQuery] = useState('');
    const [mlxSearchResults, setMlxSearchResults] = useState<any[]>([]);
    const [mlxSearching, setMlxSearching] = useState(false);
    const [mlxDownloading, setMlxDownloading] = useState<string | null>(null);
    const [mlxProgress, setMlxProgress] = useState<{ percent: number, bytes: number, total: number } | null>(null);
    const [mlxConfig, setMlxConfig] = useState<{ temperature: number, top_p: number, max_tokens: number }>({ temperature: 0.7, top_p: 0.9, max_tokens: 32768 });
    const [mlxConfigSaving, setMlxConfigSaving] = useState(false);

    // New features state
    const [explainLevel, setExplainLevel] = useState<'beginner' | 'intermediate' | 'expert'>('intermediate');
    const [agentModels, setAgentModels] = useState<Record<string, string>>({});
    const [theme, setTheme] = useState<'dark' | 'light'>(
        () => (localStorage.getItem('mq-theme') as 'dark' | 'light') || 'dark'
    );

    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (mlxDownloading) {
            interval = setInterval(() => {
                import('../../services/api').then(({ fetchMLXPullStatus }) => {
                    fetchMLXPullStatus().then(status => {
                        if (status && status.status === 'downloading') {
                            setMlxProgress({
                                percent: status.progress_percent || 0,
                                bytes: status.downloaded_bytes || 0,
                                total: status.total_bytes || 0
                            });
                        } else if (status && (status.status === 'complete' || status.status === 'failed' || status.status === 'idle')) {
                            setMlxProgress(null);
                        }
                    }).catch(() => { });
                });
            }, 500);
        } else {
            setMlxProgress(null);
        }
        return () => clearInterval(interval);
    }, [mlxDownloading]);

    useEffect(() => {
        if (!isOpen) return;
        fetchSettings().then((data) => {
            setModel(data.ollama_model || '');
            setShots(data.default_shots || 1024);
            setOllamaUrl(data.ollama_url || '');
            setPlatform(data.platform || {});
            if (data.explain_level) setExplainLevel(data.explain_level);
            if (data.agent_models) setAgentModels(data.agent_models);
            if (data.cloud_provider?.provider) {
                setSavedProvider(data.cloud_provider.provider);
                if (data.cloud_provider.provider !== 'ollama') {
                    setActiveProvider(data.cloud_provider.provider);
                    setCloudModel(data.cloud_provider.model || '');
                }
            }
            if (data.platform?.os === 'Darwin') {
                fetchMLXModels().then(mlxData => {
                    setMlxModels(mlxData.models || []);
                    setActiveMlxModel(mlxData.current || '');
                }).catch(() => { });

                // Fetch current MLX generation config
                import('../../services/api').then(({ fetchMLXConfig }) => {
                    fetchMLXConfig().then(config => {
                        if (config) setMlxConfig(config);
                    }).catch(() => { });
                });
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
        try {
            await updateSettings({
                ollama_model: model,
                default_shots: shots,
                ollama_url: ollamaUrl,
                explain_level: explainLevel,
            });
            // Save agent models separately
            const token = localStorage.getItem('mq_token');
            await fetch('/api/settings/agent-models', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({ agent_models: agentModels }),
            });
            // Apply theme
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('mq-theme', theme);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (error) {
            console.error("Failed to save settings", error);
        } finally {
            setSaving(false);
        }
    };

    const handleCloudSave = async () => {
        setCloudSaving(true);

        // Extract API key if user typed it before hitting Save
        const input = document.getElementById('cloud-api-key-input') as HTMLInputElement;
        const apiKey = input?.value || undefined;

        await setCloudProvider(activeProvider, cloudModel || undefined, apiKey);

        if (apiKey && input) {
            input.value = '';
            fetchCloudProviders().then((data) => setProviders(data.providers || []));
        }

        setSavedProvider(activeProvider);
        setCloudSaving(false);
        setCloudSaved(true);
        setTimeout(() => setCloudSaved(false), 2000);
    };

    const handleMlxSearch = async () => {
        if (!mlxSearchQuery.trim()) return;
        setMlxSearching(true);
        try {
            const data = await searchMLXModels(mlxSearchQuery);
            setMlxSearchResults(data.results || []);
        } catch (e) {
            console.error("MLX Search failed", e);
        } finally {
            setMlxSearching(false);
        }
    };

    const handleMlxPull = async (modelId: string) => {
        setMlxDownloading(modelId);
        try {
            await pullMLXModel(modelId);
            setActiveMlxModel(modelId);
            const mlxData = await fetchMLXModels();
            setMlxModels(mlxData.models || []);
        } catch (e) {
            console.error("Failed to pull MLX model", e);
        } finally {
            setMlxDownloading(null);
        }
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
                    {platform.os === 'Darwin' && (
                        <button
                            onClick={() => setActiveTab('mlx')}
                            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer
                                ${activeTab === 'mlx'
                                    ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white border border-purple-500/30'
                                    : 'text-[#636370] hover:text-white hover:bg-white/[0.04]'
                                }`}
                        >🍏 Apple MLX</button>
                    )}
                </div>

                {/* Body */}
                <div className="px-6 py-5 space-y-5 overflow-y-auto flex-1">
                    {activeTab === 'mlx' ? (
                        <>
                            <div className="p-4 rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-[#0c0c14]">
                                <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
                                    <span className="text-xl">⚡</span> Apple Silicon Native (MLX)
                                </h3>
                                <p className="text-xs text-[#a1a1aa] mb-4">
                                    Bypass Ollama and run native huggingface `.safetensors` models directly on your Mac's unified memory for maximum token generation speeds.
                                </p>

                                <div className="mb-4">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <label className="block text-xs font-medium text-[#a1a1aa] uppercase tracking-wider">Active MLX Model</label>
                                        <button
                                            onClick={async () => {
                                                const { unloadMLXModel } = await import('../../services/api');
                                                await unloadMLXModel();
                                                setActiveMlxModel('');
                                            }}
                                            disabled={!activeMlxModel}
                                            className="text-[10px] text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed bg-red-400/10 hover:bg-red-400/20 px-2 py-0.5 rounded transition-colors"
                                        >
                                            Unload from Memory
                                        </button>
                                    </div>
                                    <div className="w-full px-3 py-2.5 rounded-xl bg-black/40 border border-white/[0.08] text-[#3ecfef] text-sm font-mono truncate">
                                        {activeMlxModel || "No model currently loaded"}
                                    </div>
                                </div>

                                {activeMlxModel && (
                                    <div className="mb-4 p-3 rounded-lg border border-white/[0.06] bg-black/20">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-xs font-medium text-white">Generation Config</span>
                                            <button
                                                onClick={async () => {
                                                    setMlxConfigSaving(true);
                                                    const { updateMLXConfig } = await import('../../services/api');
                                                    await updateMLXConfig(mlxConfig);
                                                    setMlxConfigSaving(false);
                                                }}
                                                className="px-2 py-1 text-[10px] rounded bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors"
                                            >
                                                {mlxConfigSaving ? 'Saving...' : 'Save Config'}
                                            </button>
                                        </div>
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between gap-4">
                                                <div className="flex-1">
                                                    <label className="text-[10px] text-[#a1a1aa] flex justify-between">
                                                        <span>Temperature</span>
                                                        <span>{mlxConfig.temperature.toFixed(2)}</span>
                                                    </label>
                                                    <input
                                                        type="range" min="0" max="2" step="0.05"
                                                        value={mlxConfig.temperature}
                                                        onChange={e => setMlxConfig({ ...mlxConfig, temperature: parseFloat(e.target.value) })}
                                                        className="w-full mt-1 accent-purple-500"
                                                    />
                                                </div>
                                                <div className="flex-1">
                                                    <label className="text-[10px] text-[#a1a1aa] flex justify-between">
                                                        <span>Top P</span>
                                                        <span>{mlxConfig.top_p.toFixed(2)}</span>
                                                    </label>
                                                    <input
                                                        type="range" min="0" max="1" step="0.05"
                                                        value={mlxConfig.top_p}
                                                        onChange={e => setMlxConfig({ ...mlxConfig, top_p: parseFloat(e.target.value) })}
                                                        className="w-full mt-1 accent-purple-500"
                                                    />
                                                </div>
                                            </div>
                                            <div>
                                                <label className="text-[10px] text-[#a1a1aa] flex justify-between">
                                                    <span>Max Tokens</span>
                                                    <span>{mlxConfig.max_tokens}</span>
                                                </label>
                                                <input
                                                    type="range" min="128" max="32768" step="128"
                                                    value={mlxConfig.max_tokens}
                                                    onChange={e => setMlxConfig({ ...mlxConfig, max_tokens: parseInt(e.target.value) })}
                                                    className="w-full mt-1 accent-purple-500"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-xs font-medium text-[#a1a1aa] mb-1.5 uppercase tracking-wider">Local Cache ({mlxModels.length})</label>
                                    <div className="flex flex-col gap-2 max-h-32 overflow-y-auto pr-2">
                                        {mlxModels.length === 0 ? (
                                            <span className="text-xs text-[#636370] italic">No MLX models discovered in ~/.cache/huggingface/hub/</span>
                                        ) : (
                                            mlxModels.map(m => (
                                                <div key={m} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04]">
                                                    <span className="text-xs text-white  truncate max-w-[200px]">{m}</span>
                                                    <button
                                                        disabled={activeMlxModel === m || mlxDownloading !== null}
                                                        onClick={() => handleMlxPull(m)}
                                                        className="px-2 py-1 text-[10px] font-medium rounded-lg bg-white/[0.05] text-white hover:bg-white/[0.1] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                    >
                                                        {mlxDownloading === m ? 'Loading...' : (activeMlxModel === m ? 'Loaded' : 'Load')}
                                                    </button>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="pt-2">
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">Search Hugging Face (mlx-community)</label>
                                <div className="flex gap-2">
                                    <input
                                        value={mlxSearchQuery}
                                        onChange={(e) => setMlxSearchQuery(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                handleMlxSearch();
                                            }
                                        }}
                                        placeholder="E.g. Llama-3-8B-Instruct-4bit"
                                        className="flex-1 px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                            text-white text-sm focus:outline-none focus:border-purple-500/50 transition-colors"
                                    />
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.preventDefault();
                                            handleMlxSearch();
                                        }}
                                        disabled={mlxSearching || !mlxSearchQuery}
                                        className="px-4 py-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 font-medium text-sm transition-colors disabled:opacity-50"
                                    >
                                        {mlxSearching ? 'Searching...' : 'Search'}
                                    </button>
                                </div>
                            </div>

                            {mlxSearchResults.length > 0 && (
                                <div className="mt-4 flex flex-col gap-2">
                                    <span className="text-xs text-[#636370] uppercase tracking-wider font-medium">Results From Hugging Face Hub (Live)</span>
                                    <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                                        {mlxSearchResults.map((m) => {
                                            const isDownloadingThis = mlxDownloading === m.id;
                                            const progressPercent = isDownloadingThis && mlxProgress ? mlxProgress.percent : 0;

                                            return (
                                                <div key={m.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between hover:border-purple-500/30 transition-colors">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm text-white font-medium">{m.id.split('/')[1]}</span>
                                                        <span className="text-[10px] text-[#636370]">
                                                            {m.id.split('/')[0]} · {m.downloads} DLs
                                                            {m.size_mb ? ` · ${m.size_mb >= 1024 ? (m.size_mb / 1024).toFixed(1) + ' GB' : m.size_mb + ' MB'}` : ''}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {mlxModels.includes(m.id) && <span className="text-[10px] text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full border border-green-400/20">Cached</span>}
                                                        <button
                                                            disabled={mlxDownloading !== null}
                                                            onClick={() => handleMlxPull(m.id)}
                                                            className={`relative overflow-hidden px-3 py-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer disabled:opacity-80 flex items-center gap-1 ${isDownloadingThis ? 'bg-purple-900/50 text-white w-24 justify-center' : 'bg-white text-black hover:bg-white/90 disabled:opacity-50'}`}
                                                        >
                                                            {isDownloadingThis && (
                                                                <div
                                                                    className="absolute left-0 top-0 bottom-0 bg-purple-500/50 transition-all duration-300"
                                                                    style={{ width: `${progressPercent}%` }}
                                                                />
                                                            )}
                                                            <span className="relative z-10 flex items-center gap-1">
                                                                {isDownloadingThis ? (
                                                                    <>⏳ <span>{progressPercent}%</span></>
                                                                ) : (
                                                                    <>⬇ <span>Pull</span></>
                                                                )}
                                                            </span>
                                                        </button>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : activeTab === 'local' ? (
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
                                        <option value="" className="bg-[#0c0c14] text-[#3ecfef]">✨ Auto-detect latest model</option>
                                        {models.map((m) => (
                                            <option key={m} value={m} className="bg-[#0c0c14]">{m}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <input
                                        value={model}
                                        onChange={(e) => setModel(e.target.value)}
                                        placeholder="Auto-detecting latest..."
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

                            {/* ── Explain Level ──────────────────── */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-2">Explain Level</label>
                                <div className="flex gap-1.5">
                                    {(['beginner', 'intermediate', 'expert'] as const).map((level) => (
                                        <button
                                            key={level}
                                            onClick={() => setExplainLevel(level)}
                                            className={`flex-1 py-2 px-3 rounded-xl text-xs font-medium transition-all cursor-pointer
                                                ${explainLevel === level
                                                    ? 'bg-[#3ecfef]/10 text-[#3ecfef] border border-[#3ecfef]/30'
                                                    : 'bg-white/[0.03] text-[#636370] border border-white/[0.06] hover:text-[#a1a1aa]'}`}
                                        >
                                            {level === 'beginner' ? '🎓' : level === 'intermediate' ? '📊' : '🔬'}{' '}
                                            {level.charAt(0).toUpperCase() + level.slice(1)}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-[10px] text-[#636370] mt-1">
                                    {explainLevel === 'beginner'
                                        ? 'Detailed explanations with analogies'
                                        : explainLevel === 'expert'
                                            ? 'Concise, technical responses'
                                            : 'Balanced depth and clarity'}
                                </p>
                            </div>

                            {/* ── Agent Models ──────────────────── */}
                            {models.length > 0 && (
                                <div>
                                    <label className="block text-sm font-medium text-[#a1a1aa] mb-2">Per-Agent Models</label>
                                    <div className="space-y-1.5">
                                        {['code', 'research', 'chemistry', 'finance', 'optimization'].map((agent) => (
                                            <div key={agent} className="flex items-center gap-2">
                                                <span className="text-xs text-[#636370] w-20 capitalize">{agent}</span>
                                                <select
                                                    value={agentModels[agent] || ''}
                                                    onChange={(e) => setAgentModels(prev => ({
                                                        ...prev,
                                                        [agent]: e.target.value,
                                                    }))}
                                                    className="flex-1 px-2 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06]
                                                        text-[#a1a1aa] text-xs focus:outline-none focus:border-[#3ecfef]/30
                                                        transition-colors appearance-none cursor-pointer"
                                                >
                                                    <option value="" className="bg-[#0c0c14]">Default</option>
                                                    {models.map((m) => (
                                                        <option key={m} value={m} className="bg-[#0c0c14]">{m}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-[#636370] mt-1">
                                        Assign specific LLM models to each agent (e.g., CodeLlama for Code)
                                    </p>
                                </div>
                            )}

                            {/* ── Theme Toggle ──────────────────── */}
                            <div>
                                <label className="block text-sm font-medium text-[#a1a1aa] mb-2">Theme</label>
                                <div className="flex gap-1.5">
                                    <button
                                        onClick={() => setTheme('dark')}
                                        className={`flex-1 py-2 px-3 rounded-xl text-xs font-medium transition-all cursor-pointer
                                            ${theme === 'dark'
                                                ? 'bg-[#3ecfef]/10 text-[#3ecfef] border border-[#3ecfef]/30'
                                                : 'bg-white/[0.03] text-[#636370] border border-white/[0.06] hover:text-[#a1a1aa]'}`}
                                    >🌙 Dark</button>
                                    <button
                                        onClick={() => setTheme('light')}
                                        className={`flex-1 py-2 px-3 rounded-xl text-xs font-medium transition-all cursor-pointer
                                            ${theme === 'light'
                                                ? 'bg-[#3ecfef]/10 text-[#3ecfef] border border-[#3ecfef]/30'
                                                : 'bg-white/[0.03] text-[#636370] border border-white/[0.06] hover:text-[#a1a1aa]'}`}
                                    >☀️ Light</button>
                                </div>
                            </div>
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
                                        {savedProvider === 'ollama' && !activeMlxModel && <div className="text-[10px] text-green-400 mt-1">● Active</div>}
                                        {savedProvider === 'ollama' && activeMlxModel && <div className="text-[10px] text-amber-500 mt-1">● Overridden by MLX</div>}
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
                                                {p.id === 'anthropic' ? '🟠' : p.id === 'openai' ? '🟢' : p.id === 'cohere' ? '🟣' : p.id === 'mistral' ? '🔷' : p.id === 'deepseek' ? '🐋' : '🔵'} {p.name}
                                            </div>
                                            <div className="text-[10px] text-[#636370] mt-0.5">
                                                {p.models.length} models
                                            </div>
                                            <div className={`text-[10px] mt-1 ${savedProvider === p.id ? 'text-green-400' : p.configured ? 'text-[#3ecfef]' : 'text-[#636370]'}`}>
                                                {savedProvider === p.id ? '● Active' : p.configured ? '✓ Key set' : '○ Not configured'}
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
                                                placeholder={`Enter ${{
                                                    anthropic: 'ANTHROPIC_API_KEY', openai: 'OPENAI_API_KEY',
                                                    gemini: 'GOOGLE_API_KEY', cohere: 'COHERE_API_KEY',
                                                    mistral: 'MISTRAL_API_KEY', deepseek: 'DEEPSEEK_API_KEY',
                                                }[activeProvider] || 'API_KEY'}`}
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
                                                            cohere: 'cohere_api_key',
                                                            mistral: 'mistral_api_key',
                                                            deepseek: 'deepseek_api_key',
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
                                                    {{
                                                        anthropic: 'ANTHROPIC_API_KEY', openai: 'OPENAI_API_KEY',
                                                        gemini: 'GOOGLE_API_KEY', cohere: 'COHERE_API_KEY',
                                                        mistral: 'MISTRAL_API_KEY', deepseek: 'DEEPSEEK_API_KEY',
                                                    }[activeProvider] || 'API_KEY'}
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
