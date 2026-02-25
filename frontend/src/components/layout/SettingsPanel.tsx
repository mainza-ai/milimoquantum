/* Milimo Quantum — Settings Panel */
import { useState, useEffect } from 'react';
import { fetchSettings, fetchModels, updateSettings } from '../../services/api';

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

    useEffect(() => {
        if (!isOpen) return;
        fetchSettings().then((data) => {
            setModel(data.ollama_model || '');
            setShots(data.default_shots || 1024);
            setOllamaUrl(data.ollama_url || '');
            setPlatform(data.platform || {});
        }).catch(() => { });

        fetchModels().then((data) => {
            setModels(data.models || []);
        }).catch(() => { });
    }, [isOpen]);

    const handleSave = async () => {
        setSaving(true);
        await updateSettings({ ollama_model: model, default_shots: shots, ollama_url: ollamaUrl });
        setSaving(false);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div
                className="w-full max-w-md rounded-2xl border border-white/[0.08]
                    bg-gradient-to-b from-[#0c0c14] to-[#060610]
                    shadow-2xl shadow-black/50 overflow-hidden"
                style={{ animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
                    <h2 className="text-lg font-semibold text-white tracking-tight">Settings</h2>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-lg
                            hover:bg-white/[0.06] text-[#636370] hover:text-white transition-all"
                    >✕</button>
                </div>

                {/* Body */}
                <div className="px-6 py-5 space-y-5">
                    {/* Model Selector */}
                    <div>
                        <label className="block text-sm font-medium text-[#a1a1aa] mb-1.5">LLM Model</label>
                        {models.length > 0 ? (
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="w-full px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08]
                                    text-white text-sm focus:outline-none focus:border-[#3ecfef]/40
                                    transition-colors appearance-none"
                            >
                                {models.map((m) => (
                                    <option key={m} value={m} className="bg-[#0c0c14]">{m}</option>
                                ))}
                            </select>
                        ) : (
                            <input
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                placeholder="llama3.2"
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
                            type="range"
                            min="100"
                            max="8192"
                            step="100"
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
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.06]">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-xl text-sm text-[#a1a1aa]
                            hover:bg-white/[0.04] transition-colors"
                    >Cancel</button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-5 py-2 rounded-xl text-sm font-medium
                            bg-gradient-to-r from-[#3ecfef]/20 to-[#5bb8d4]/20
                            border border-[#3ecfef]/20 text-[#3ecfef]
                            hover:from-[#3ecfef]/30 hover:to-[#5bb8d4]/30
                            transition-all active:scale-[0.98]"
                    >{saved ? '✓ Saved' : saving ? 'Saving...' : 'Save'}</button>
                </div>
            </div>
        </div>
    );
}
