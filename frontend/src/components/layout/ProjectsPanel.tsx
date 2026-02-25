/* Milimo Quantum — Project Management Panel */
import { useState, useEffect } from 'react';
import { fetchProjects, createProject, deleteProject, addConversationToProject } from '../../services/api';

interface Project {
    id: string;
    name: string;
    description: string;
    tags: string[];
    conversation_count: number;
    created_at: string;
    updated_at: string;
}

interface ProjectsPanelProps {
    isOpen: boolean;
    onClose: () => void;
    currentConversationId?: string;
}

export function ProjectsPanel({ isOpen, onClose, currentConversationId }: ProjectsPanelProps) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newTags, setNewTags] = useState('');
    const [linked, setLinked] = useState<string | null>(null);

    const refresh = () => {
        setLoading(true);
        fetchProjects()
            .then(data => setProjects(data.projects || []))
            .catch(() => { })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        if (isOpen) refresh();
    }, [isOpen]);

    const handleCreate = async () => {
        if (!newName.trim()) return;
        await createProject({
            name: newName.trim(),
            description: newDesc.trim(),
            tags: newTags.split(',').map(t => t.trim()).filter(Boolean),
        });
        setNewName('');
        setNewDesc('');
        setNewTags('');
        setShowCreate(false);
        refresh();
    };

    const handleDelete = async (id: string) => {
        await deleteProject(id);
        refresh();
    };

    const handleLink = async (projectId: string) => {
        if (!currentConversationId) return;
        await addConversationToProject(projectId, currentConversationId);
        setLinked(projectId);
        setTimeout(() => setLinked(null), 2000);
        refresh();
    };

    if (!isOpen) return null;

    const tagColors = ['#3ecfef', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#f97316'];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
                w-full max-w-2xl max-h-[85vh] overflow-hidden mx-4 flex flex-col"
                style={{ animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
                {/* Header */}
                <div className="border-b border-cyan-500/10 px-6 py-4 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">📁</span>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Projects</h2>
                            <p className="text-xs text-gray-400 mt-0.5">Organize experiments & conversations</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setShowCreate(!showCreate)}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium
                                bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                hover:bg-cyan-500/20 transition-all cursor-pointer"
                        >{showCreate ? 'Cancel' : '+ New Project'}</button>
                        <button onClick={onClose}
                            className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10
                                flex items-center justify-center text-gray-400 hover:text-white
                                transition-all cursor-pointer">✕</button>
                    </div>
                </div>

                {/* Create form */}
                {showCreate && (
                    <div className="px-6 py-4 border-b border-white/5 space-y-3">
                        <input
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            placeholder="Project name"
                            className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-2.5
                                text-sm text-white placeholder-gray-500
                                focus:outline-none focus:border-cyan-500/40 transition-colors"
                            autoFocus
                        />
                        <input
                            value={newDesc}
                            onChange={e => setNewDesc(e.target.value)}
                            placeholder="Description (optional)"
                            className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-2
                                text-sm text-white placeholder-gray-500
                                focus:outline-none focus:border-cyan-500/40 transition-colors"
                        />
                        <div className="flex gap-2">
                            <input
                                value={newTags}
                                onChange={e => setNewTags(e.target.value)}
                                placeholder="Tags (comma separated)"
                                className="flex-1 bg-white/[0.04] border border-white/10 rounded-xl px-4 py-2
                                    text-sm text-white placeholder-gray-500
                                    focus:outline-none focus:border-cyan-500/40 transition-colors"
                            />
                            <button
                                onClick={handleCreate}
                                disabled={!newName.trim()}
                                className="px-5 py-2 rounded-xl text-sm font-medium cursor-pointer
                                    bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                    hover:bg-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed
                                    transition-all"
                            >Create</button>
                        </div>
                    </div>
                )}

                {/* Project list */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12 text-gray-400">
                            <div className="animate-spin mr-3 w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" />
                            Loading projects...
                        </div>
                    ) : projects.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <div className="text-4xl mb-3">📁</div>
                            <p>No projects yet. Create one to organize your work!</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {projects.map(project => (
                                <div key={project.id}
                                    className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5
                                        hover:border-cyan-500/20 transition-all group relative"
                                >
                                    <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 via-transparent to-purple-500/0
                                        group-hover:from-cyan-500/[0.03] group-hover:to-purple-500/[0.03]
                                        rounded-xl transition-all duration-500 pointer-events-none" />

                                    <div className="flex justify-between items-start relative z-10">
                                        <div className="flex-1 min-w-0">
                                            <h3 className="text-base font-semibold text-white group-hover:text-cyan-400 transition-colors">
                                                {project.name}
                                            </h3>
                                            {project.description && (
                                                <p className="text-sm text-gray-400 mt-1 leading-relaxed">{project.description}</p>
                                            )}
                                        </div>
                                        <div className="flex gap-1.5 shrink-0 ml-3">
                                            {currentConversationId && (
                                                <button
                                                    onClick={() => handleLink(project.id)}
                                                    className="px-2.5 py-1 rounded-lg text-[10px] font-medium cursor-pointer
                                                        bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                                        hover:bg-cyan-500/20 transition-all"
                                                >{linked === project.id ? '✓ Linked' : '+ Link Chat'}</button>
                                            )}
                                            <button
                                                onClick={() => handleDelete(project.id)}
                                                className="px-2 py-1 rounded-lg text-[10px] cursor-pointer
                                                    text-gray-500 hover:text-red-400 hover:bg-red-500/10
                                                    transition-all opacity-0 group-hover:opacity-100"
                                            >✕</button>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3 mt-3 relative z-10">
                                        <span className="text-xs text-gray-500">
                                            💬 {project.conversation_count} conversation{project.conversation_count !== 1 ? 's' : ''}
                                        </span>
                                        {project.tags.length > 0 && (
                                            <div className="flex gap-1.5">
                                                {project.tags.map((tag, i) => (
                                                    <span key={tag}
                                                        className="px-2 py-0.5 rounded text-[10px] uppercase tracking-wider"
                                                        style={{
                                                            backgroundColor: `${tagColors[i % tagColors.length]}10`,
                                                            color: tagColors[i % tagColors.length],
                                                        }}
                                                    >{tag}</span>
                                                ))}
                                            </div>
                                        )}
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
