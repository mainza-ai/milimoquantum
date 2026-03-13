import React, { useState, useEffect, useMemo } from 'react';
import { KnowledgeGraph as KnowledgeGraphData, GraphNode } from '../types';

interface KnowledgeGraphProps {
  data: KnowledgeGraphData;
}

const getNodeColor = (type: GraphNode['type']) => {
  switch (type) {
    case 'candidate': return '#3b82f6'; // blue
    case 'target': return '#10b981'; // green
    case 'concept': return '#f97316'; // orange
    default: return '#6b7280'; // gray
  }
};

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ data }) => {
    const width = 380;
    const height = 300;
    const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
    const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

    const nodes = useMemo(() => data.nodes, [data.nodes]);
    const edges = useMemo(() => data.edges, [data.edges]);

    // Simple physics simulation for layout
    useEffect(() => {
        const initialPositions: Record<string, { x: number; y: number; vx: number; vy: number }> = {};
        nodes.forEach(node => {
            initialPositions[node.id] = {
                x: width / 2 + (Math.random() - 0.5) * 50,
                y: height / 2 + (Math.random() - 0.5) * 50,
                vx: 0,
                vy: 0,
            };
        });

        const simulation = () => {
            const newPositions = { ...initialPositions };

            // Apply forces
            for (let i = 0; i < 50; i++) { // iterations
                // Repulsion force between all nodes
                nodes.forEach(nodeA => {
                    nodes.forEach(nodeB => {
                        if (nodeA.id === nodeB.id) return;
                        const dx = newPositions[nodeA.id].x - newPositions[nodeB.id].x;
                        const dy = newPositions[nodeA.id].y - newPositions[nodeB.id].y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        if (distance > 0) {
                            const force = 1000 / (distance * distance);
                            newPositions[nodeA.id].vx += (dx / distance) * force;
                            newPositions[nodeA.id].vy += (dy / distance) * force;
                        }
                    });
                });

                // Spring force for edges
                edges.forEach(edge => {
                    const source = newPositions[edge.from];
                    const target = newPositions[edge.to];
                    if (!source || !target) return;
                    const dx = target.x - source.x;
                    const dy = target.y - source.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const force = 0.03 * (distance - 120);
                    source.vx += (dx / distance) * force;
                    source.vy += (dy / distance) * force;
                    target.vx -= (dx / distance) * force;
                    target.vy -= (dy / distance) * force;
                });

                // Gravity to center
                nodes.forEach(node => {
                    const pos = newPositions[node.id];
                    pos.vx += (width / 2 - pos.x) * 0.005;
                    pos.vy += (height / 2 - pos.y) * 0.005;
                });


                // Update positions
                nodes.forEach(node => {
                    const pos = newPositions[node.id];
                    pos.vx *= 0.95; // damping
                    pos.vy *= 0.95;
                    pos.x += pos.vx;
                    pos.y += pos.vy;

                    // Boundary check
                    pos.x = Math.max(20, Math.min(width - 20, pos.x));
                    pos.y = Math.max(20, Math.min(height - 20, pos.y));
                });
            }

            const finalPositions: Record<string, { x: number; y: number }> = {};
            Object.keys(newPositions).forEach(id => {
                finalPositions[id] = { x: newPositions[id].x, y: newPositions[id].y };
            });
            setPositions(finalPositions);
        };

        if (nodes.length > 0) {
            simulation();
        }
    }, [nodes, edges, width, height]);

    if (nodes.length === 0) {
        return <div className="text-center text-sm text-neutral-400">No knowledge graph data available.</div>;
    }
    
    const isNodeRelatedToHovered = (nodeId: string) => {
        if (!hoveredNodeId) return false;
        if (nodeId === hoveredNodeId) return true;
        return edges.some(edge => 
            (edge.from === hoveredNodeId && edge.to === nodeId) ||
            (edge.to === hoveredNodeId && edge.from === nodeId)
        );
    }
    
    const isEdgeRelatedToHovered = (edge: any) => {
        if (!hoveredNodeId) return false;
        return edge.from === hoveredNodeId || edge.to === hoveredNodeId;
    }

    return (
        <svg width={width} height={height} className="font-sans text-xs">
            <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
                    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
                </marker>
            </defs>
            {edges.map((edge, i) => {
                const source = positions[edge.from];
                const target = positions[edge.to];
                if (!source || !target) return null;
                 const isRelated = isEdgeRelatedToHovered(edge);

                return (
                     <g key={i} className={`transition-opacity duration-200 ${hoveredNodeId && !isRelated ? 'opacity-20' : 'opacity-100'}`}>
                        <line
                            x1={source.x} y1={source.y}
                            x2={target.x} y2={target.y}
                            stroke="#6b7280"
                            strokeWidth="1.5"
                            markerEnd="url(#arrow)"
                        />
                         <text
                            x={(source.x + target.x) / 2}
                            y={(source.y + target.y) / 2 - 5}
                            textAnchor="middle"
                            fill="#a1a1aa"
                            className="text-[10px] bg-neutral-800 px-1"
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

                return (
                    <g
                        key={node.id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        className={`cursor-pointer transition-opacity duration-200 ${hoveredNodeId && !isRelated ? 'opacity-20' : 'opacity-100'}`}
                        onMouseOver={() => setHoveredNodeId(node.id)}
                        onMouseOut={() => setHoveredNodeId(null)}
                    >
                        <circle
                            r="8"
                            fill={getNodeColor(node.type)}
                            stroke="#171717"
                            strokeWidth="3"
                        />
                         <text
                            y="-12"
                            textAnchor="middle"
                            fill="#e5e5e5"
                            className="font-semibold"
                        >
                            {node.label}
                        </text>
                    </g>
                );
            })}
        </svg>
    );
};

export default KnowledgeGraph;
