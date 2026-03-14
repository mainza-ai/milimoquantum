
import React, { useState } from 'react';
import type { Molecule } from '../types';

interface CandidateComparisonChartProps {
  molecules: Molecule[];
  onMoleculeClick: (molecule: Molecule) => void;
  selectedMolecule: Molecule | null;
}

const CandidateComparisonChart: React.FC<CandidateComparisonChartProps> = ({ molecules, onMoleculeClick, selectedMolecule }) => {
  const [tooltip, setTooltip] = useState<{ content: string; x: number; y: number } | null>(null);

  if (!molecules || molecules.length === 0) {
    return <div className="h-full flex items-center justify-center text-mq-text-tertiary font-mono text-xs uppercase tracking-widest">Insufficient candidate data</div>;
  }

  const width = 600;
  const height = 400;
  const margin = { top: 40, right: 40, bottom: 60, left: 70 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const toxicityScores = molecules.map(m => m.admet?.toxicity.score ?? 0);
  const bindingEnergies = molecules.map(m => m.bindingEnergy ?? 0);
  const saScores = molecules.map(m => m.saScore ?? 5);
  
  const xMin = 0;
  const xMax = Math.max(1.0, ...toxicityScores);
  const yMin = Math.min(...bindingEnergies) - 2;
  const yMax = Math.max(...bindingEnergies) + 2;
  const saMin = Math.min(...saScores);
  const saMax = Math.max(...saScores);

  const xScale = (value: number) => (value - xMin) / (xMax - xMin) * innerWidth;
  const yScale = (value: number) => innerHeight - ((value - yMin) / (yMax - yMin) * innerHeight);

  const radiusScale = (value: number) => {
    const minRadius = 6;
    const maxRadius = 12;
    if (saMax === saMin) return (minRadius + maxRadius) / 2;
    return maxRadius - ((value - saMin) / (saMax - saMin)) * (maxRadius - minRadius);
  };

  const handleMouseOver = (molecule: Molecule, e: React.MouseEvent<SVGCircleElement>) => {
    const svg = e.currentTarget.ownerSVGElement;
    if (!svg) return;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    
    const point = svg.createSVGPoint();
    point.x = e.currentTarget.cx.baseVal.value;
    point.y = e.currentTarget.cy.baseVal.value;
    const transformedPoint = point.matrixTransform(e.currentTarget.getCTM()!);
    
    setTooltip({
      content: `${molecule.name}: BE=${molecule.bindingEnergy?.toFixed(2)}, Tox=${molecule.admet?.toxicity.score?.toFixed(2)}`,
      x: transformedPoint.x,
      y: transformedPoint.y - 15
    });
  };
  
  const handleMouseOut = () => {
    setTooltip(null);
  };

  return (
    <div className="relative w-full h-full bg-mq-void/20 rounded-2xl border border-mq-border flex flex-col p-6">
        <div className="flex-1 min-h-0">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
                <g transform={`translate(${margin.left}, ${margin.top})`}>
                    {/* Grid Lines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
                        <line key={`gx-${i}`} x1={xScale(p * xMax)} y1={0} x2={xScale(p * xMax)} y2={innerHeight} stroke="#1e293b" strokeWidth="1" />
                    ))}
                    {[0, 0.25, 0.5, 0.75, 1].map((p, i) => {
                        const val = yMin + p * (yMax-yMin);
                        return <line key={`gy-${i}`} x1={0} y1={yScale(val)} x2={innerWidth} y2={yScale(val)} stroke="#1e293b" strokeWidth="1" />;
                    })}

                    {/* Axes */}
                    <line x1="0" y1={innerHeight} x2={innerWidth} y2={innerHeight} stroke="#475569" strokeWidth="2" />
                    <line x1="0" y1="0" x2="0" y2={innerHeight} stroke="#475569" strokeWidth="2" />
                    
                    {/* Labels */}
                    <text x={innerWidth / 2} y={innerHeight + 45} textAnchor="middle" fill="#64748b" className="text-[11px] font-bold uppercase tracking-widest">
                        Toxicity Score (Lower is better)
                    </text>
                    <text transform={`rotate(-90)`} x={-innerHeight / 2} y={-45} textAnchor="middle" fill="#64748b" className="text-[11px] font-bold uppercase tracking-widest">
                        Binding Energy (kJ/mol)
                    </text>

                    {/* Optimal Quadrant Highlight */}
                    <rect x={xScale(0)} y={yScale(yMax)} width={innerWidth/4} height={innerHeight/4} fill="rgba(16, 185, 129, 0.05)" stroke="rgba(16, 185, 129, 0.2)" strokeDasharray="4 4" />
                    <text x={10} y={20} fill="#10b981" className="text-[10px] font-bold opacity-60 uppercase tracking-tighter">Gold Standard Zone</text>
                    
                    {/* Data Points */}
                    {molecules.map((mol, i) => {
                        const cx = xScale(mol.admet?.toxicity.score ?? 0);
                        const cy = yScale(mol.bindingEnergy ?? 0);
                        const r = radiusScale(mol.saScore ?? 5);
                        const isSelected = mol.smiles === selectedMolecule?.smiles;

                        return (
                            <circle
                                key={i}
                                cx={cx}
                                cy={cy}
                                r={isSelected ? r + 3 : r}
                                fill={isSelected ? '#3ecfef' : '#334155'}
                                stroke={isSelected ? '#fff' : '#475569' }
                                strokeWidth={isSelected ? '2.5' : '1.5'}
                                className="transition-all duration-300 cursor-pointer"
                                style={{ 
                                    opacity: isSelected ? 1 : (selectedMolecule ? 0.3 : 0.8),
                                    filter: isSelected ? 'drop-shadow(0 0 8px rgba(62, 207, 239, 0.4))' : 'none'
                                }}
                                onMouseOver={(e) => handleMouseOver(mol, e)}
                                onMouseOut={handleMouseOut}
                                onClick={() => onMoleculeClick(mol)}
                            />
                        );
                    })}
                </g>
            </svg>
        </div>
        <div className="mt-4 flex items-center justify-between px-2 text-[10px] font-mono text-mq-text-tertiary uppercase tracking-widest border-t border-mq-border/30 pt-4">
            <span>● Size = Synthesizability (Larger is easier)</span>
            <div className="flex gap-4">
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#10b981]/20" /> Leading Candidate</span>
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-mq-cyan" /> Selected</span>
            </div>
        </div>
        {tooltip && (
            <div
                className="absolute bg-mq-surface border border-mq-border text-mq-text text-[11px] font-bold px-3 py-1.5 rounded-lg pointer-events-none transform -translate-x-1/2 -translate-y-full shadow-2xl z-50 animate-fade-in"
                style={{ left: tooltip.x, top: tooltip.y }}
            >
                {tooltip.content}
            </div>
        )}
    </div>
  );
};

export default CandidateComparisonChart;
