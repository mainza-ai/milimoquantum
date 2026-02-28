import React, { useState } from 'react';

interface WorkflowTask {
    id: string;
    name: string;
    type: string;
    dependencies: string[];
}

export const WorkflowBuilder: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [tasks] = useState<WorkflowTask[]>([
        { id: '1', name: 'Initialize GHZ State', type: 'circuit', dependencies: [] },
        { id: '2', name: 'ZNE Error Mitigation', type: 'mitigation', dependencies: ['1'] },
        { id: '3', name: 'Analyze Fidelity', type: 'analysis', dependencies: ['2'] }
    ]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#0b0e14] border border-cyan-500/20 rounded-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="px-6 py-4 border-b border-cyan-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="text-cyan-400">⛓️</span> Quantum Workflow Designer
                        </h3>
                        <p className="text-xs text-gray-400 mt-1">Design Directed Acyclic Graphs (DAG) for automated quantum execution</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">✕</button>
                </div>

                {/* Canvas Area */}
                <div className="flex-1 overflow-auto bg-[#05070a] relative p-8">
                    <div className="flex flex-col gap-12 items-center">
                        {tasks.map((task, idx) => (
                            <React.Fragment key={task.id}>
                                <div
                                    className="w-64 p-4 rounded-xl border border-cyan-500/30 bg-[#0d1117] relative group hover:border-cyan-400/60 transition-all shadow-lg"
                                >
                                    <div className="absolute -top-3 left-4 px-2 py-0.5 rounded bg-cyan-900/50 border border-cyan-500/30 text-[10px] uppercase font-bold text-cyan-300">
                                        {task.type}
                                    </div>
                                    <h4 className="text-sm font-medium text-white mb-2">{task.name}</h4>
                                    <div className="flex gap-2">
                                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                        <span className="text-[10px] text-gray-500">Ready</span>
                                    </div>

                                    {/* Connectors */}
                                    {idx < tasks.length - 1 && (
                                        <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 h-12 w-0.5 bg-cyan-500/20 group-hover:bg-cyan-500/40 transition-colors">
                                            <div className="absolute bottom-0 -left-1 w-2.5 h-2.5 border-b-2 border-r-2 border-cyan-500/40 -rotate-45"></div>
                                        </div>
                                    )}
                                </div>
                            </React.Fragment>
                        ))}

                        <button
                            className="mt-4 px-6 py-3 rounded-xl border-2 border-dashed border-cyan-500/20 text-cyan-500/60 hover:border-cyan-500/40 hover:text-cyan-400 transition-all flex items-center gap-2 text-sm"
                            onClick={() => { }}
                        >
                            <span>+</span> Add Task Node
                        </button>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-cyan-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Nodes: {tasks.length}</span>
                        <span>Est. Execution Time: ~42s</span>
                    </div>
                    <div className="flex gap-3">
                        <button className="px-4 py-2 text-sm font-medium text-gray-400 border border-white/5 rounded-lg hover:bg-white/5 transition-colors">Save Draft</button>
                        <button
                            className="px-6 py-2 text-sm font-bold text-black bg-cyan-400 rounded-lg hover:bg-cyan-300 transition-colors shadow-[0_0_15px_rgba(34,211,238,0.4)]"
                        >
                            Deploy Pipeline
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
