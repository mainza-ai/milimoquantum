
import React, { useState, useEffect, useMemo } from 'react';
import type { KnowledgeGraph as KnowledgeGraphData, GraphNode } from '../types';

interface KnowledgeGraphProps {
  data: KnowledgeGraphData;
}

const getNodeColor = (type: GraphNode['type']) => {
  switch (type) {
    case 'candidate': return '#3ecfef'; // cyan
    case 'target': return '#10b981'; // green
    case 'concept': return '#f59e0b'; // amber
    default: return '#94a3b8'; // gray
  }
};

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ data }) => {
    const width = 600;
    const height = 400;
    const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
    const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

    const nodes = useMemo(() => data.nodes || [], [data.nodes]);
    const edges = useMemo(() => data.edges || [], [data.edges]);

    useEffect(() => {
        if (!nodes.length) return;

        const initialPositions: Record<string, { x: number; y: number; vx: number; vy: number }> = {};
        nodes.forEach(node => {
            initialPositions[node.id] = {
                x: width / 2 + (Math.random() - 0.5) * 100,
                y: height / 2 + (Math.random() - 0.5) * 100,
                vx: 0,
                vy: 0,
            };
        });

        const simulation = () => {
            const newPositions = { ...initialPositions };

            for (let i = 0; i < 60; i++) {
                nodes.forEach(nodeA => {
                    nodes.forEach(nodeB => {
                        if (nodeA.id === nodeB.id) return;
                        const dx = newPositions[nodeA.id].x - newPositions[nodeB.id].x;
                        const dy = newPositions[nodeA.id].y - newPositions[nodeB.id].y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        if (distance > 0) {
                            const force = 1200 / (distance * distance);
                            newPositions[nodeA.id].vx += (dx / distance) * force;
                            newPositions[nodeA.id].vy += (dy / distance) * force;
                        }
                    });
                });

                edges.forEach(edge => {
                    const source = newPositions[edge.from];
                    const target = newPositions[edge.to];
                    if (!source || !target) return;
                    const dx = target.x - source.x;
                    const dy = target.y - source.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const force = 0.04 * (distance - 150);
                    source.vx += (dx / distance) * force;
                    source.vy += (dy / distance) * force;
                    target.vx -= (dx / distance) * force;
                    target.vy -= (dy / distance) * force;
                });

                nodes.forEach(node => {
                    const pos = newPositions[node.id];
                    pos.vx += (width / 2 - pos.x) * 0.006;
                    pos.vy += (height / 2 - pos.y) * 0.006;
                });

                nodes.forEach(node => {
                    const pos = newPositions[node.id];
                    pos.vx *= 0.94;
                    pos.vy *= 0.94;
                    pos.x += pos.vx;
                    pos.y += pos.vy;

                    pos.x = Math.max(40, Math.min(width - 40, pos.x));
                    pos.y = Math.max(40, Math.min(height - 40, pos.y));
                });
            }

            const finalPositions: Record<string, { x: number; y: number }> = {};
            Object.keys(newPositions).forEach(id => {
                finalPositions[id] = { x: newPositions[id].x, y: newPositions[id].y };
            });
            setPositions(finalPositions);
        };

        simulation();
    }, [nodes, edges, width, height]);

    if (nodes.length === 0) {
        return <div className="h-full flex items-center justify-center text-mq-text-tertiary font-mono text-xs uppercase tracking-widest">No concept nodes generated</div>;
    }
    
    const isNodeRelatedToHovered = (nodeId: string) => {
        if (!hoveredNodeId) return true;
        if (nodeId === hoveredNodeId) return true;
        return edges.some(edge => 
            (edge.from === hoveredNodeId && edge.to === nodeId) ||
            (edge.to === hoveredNodeId && edge.from === nodeId)
        );
    }
    
    const isEdgeRelatedToHovered = (edge: any) => {
        if (!hoveredNodeId) return true;
        return edge.from === hoveredNodeId || edge.to === hoveredNodeId;
    }

    return (
        <div className="w-full h-full flex items-center justify-center bg-mq-void/20 rounded-2xl overflow-hidden border border-mq-border">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full max-h-[500px]">
                <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
                        markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                    </marker>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>
                {edges.map((edge, i) => {
                    const source = positions[edge.from];
                    const target = positions[edge.to];
                    if (!source || !target) return null;
                    const isRelated = isEdgeRelatedToHovered(edge);

                    return (
                        <g key={i} className={`transition-opacity duration-300 ${hoveredNodeId && !isRelated ? 'opacity-10' : 'opacity-100'}`}>
                            <line
                                x1={source.x} y1={source.y}
                                x2={target.x} y2={target.y}
                                stroke="#334155"
                                strokeWidth="1.5"
                                markerEnd="url(#arrow)"
                                strokeDasharray="4 2"
                            />
                            <text
                                x={(source.x + target.x) / 2}
                                y={(source.y + target.y) / 2 - 8}
                                textAnchor="middle"
                                fill="#94a3b8"
                                className="text-[10px] font-mono pointer-events-none"
                            >
                                {edge.label}
                            </text>
                        </g>
                    );
                })}
                {nodes.map(node => {
                    const pos = positions[node.id];
                    if (!pos) return null;
                    const isRelated = isNodeRelatedToHovered(node.id);
                    const color = getNodeColor(node.type);

                    return (
                        <g
                            key={node.id}
                            transform={`translate(${pos.x}, ${pos.y})`}
                            className={`cursor-pointer transition-all duration-300 ${hoveredNodeId && !isRelated ? 'opacity-10 scale-90' : 'opacity-100'}`}
                            onMouseOver={() => setHoveredNodeId(node.id)}
                            onMouseOut={() => setHoveredNodeId(null)}
                        >
                            <circle
                                r="10"
                                fill={color}
                                stroke="#12121e"
                                strokeWidth="3"
                                filter={hoveredNodeId === node.id ? "url(#glow)" : undefined}
                            />
                            <text
                                y="-18"
                                textAnchor="middle"
                                fill={hoveredNodeId === node.id ? "#fff" : "#cbd5e1"}
                                className={`text-[11px] font-bold tracking-tight transition-colors ${hoveredNodeId === node.id ? 'opacity-100' : 'opacity-80'}`}
                            >
                                {node.label}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};

export default KnowledgeGraph;
