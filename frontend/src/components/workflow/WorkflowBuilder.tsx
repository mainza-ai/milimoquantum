import React, { useState, useCallback } from 'react';
import { fetchWithAuth } from '../../services/api';
import {
    ReactFlow,
    Controls,
    Background,
    applyNodeChanges,
    applyEdgeChanges,
    addEdge,
    type Node,
    type Edge,
    type NodeChange,
    type EdgeChange,
    type Connection
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes: Node[] = [
    {
        id: '1',
        type: 'default',
        data: { label: 'Initialize GHZ State [circuit]' },
        position: { x: 250, y: 50 },
        style: { background: '#0d1117', color: 'white', border: '1px solid rgba(34,211,238,0.3)', borderRadius: '8px' }
    },
    {
        id: '2',
        type: 'default',
        data: { label: 'ZNE Error Mitigation [mitigation]' },
        position: { x: 250, y: 150 },
        style: { background: '#0d1117', color: 'white', border: '1px solid rgba(34,211,238,0.3)', borderRadius: '8px' }
    },
    {
        id: '3',
        type: 'default',
        data: { label: 'Analyze Fidelity [analysis]' },
        position: { x: 250, y: 250 },
        style: { background: '#0d1117', color: 'white', border: '1px solid rgba(34,211,238,0.3)', borderRadius: '8px' }
    }
];

const initialEdges: Edge[] = [
    { id: '1-2', source: '1', target: '2', animated: true, style: { stroke: '#22d3ee' } },
    { id: '2-3', source: '2', target: '3', animated: true, style: { stroke: '#22d3ee' } }
];

export const WorkflowBuilder: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [nodes, setNodes] = useState<Node[]>(initialNodes);
    const [edges, setEdges] = useState<Edge[]>(initialEdges);

    const onNodesChange = useCallback(
        (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
        []
    );
    const onEdgesChange = useCallback(
        (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
        []
    );
    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#22d3ee' } }, eds)),
        []
    );

    const handleDeploy = async () => {
        try {
            const payload = {
                tasks: nodes.map(n => ({ id: n.id, type: n.type, label: n.data.label }))
            };
            const response = await fetchWithAuth('/api/workflows/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            alert(`Deployed Workflow ID: ${data.workflow_id}`);
            onClose();
        } catch (e) {
            console.error('Failed to deploy workflow:', e);
            alert('Deployment failed. Check console.');
        }
    };

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

                {/* React Flow Canvas Area */}
                <div className="flex-1 w-full relative bg-[#05070a]">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        colorMode="dark"
                        fitView
                    >
                        <Background gap={12} size={1} color="#22d3ee" className="opacity-10" />
                        <Controls className="bg-[#0b0e14] border-cyan-500/20 fill-white" />
                    </ReactFlow>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-cyan-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Nodes: {nodes.length}</span>
                        <span>Drag to connect nodes. Build sequential or parallel execution paths.</span>
                    </div>
                    <div className="flex gap-3">
                        <button className="px-4 py-2 text-sm font-medium text-gray-400 border border-white/5 rounded-lg hover:bg-white/5 transition-colors">Save Draft</button>
                        <button
                            onClick={handleDeploy}
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

