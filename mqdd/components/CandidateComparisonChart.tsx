
import React, { useState } from 'react';
import { Molecule } from '../types';

interface CandidateComparisonChartProps {
  molecules: Molecule[];
  onMoleculeClick: (molecule: Molecule) => void;
  selectedMolecule: Molecule | null;
}

const CandidateComparisonChart: React.FC<CandidateComparisonChartProps> = ({ molecules, onMoleculeClick, selectedMolecule }) => {
  const [tooltip, setTooltip] = useState<{ content: string; x: number; y: number } | null>(null);

  if (!molecules || molecules.length === 0) {
    return <div className="text-center text-sm text-neutral-400">Not enough data to display chart.</div>;
  }

  const width = 350;
  const height = 250;
  const margin = { top: 20, right: 20, bottom: 50, left: 50 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const toxicityScores = molecules.map(m => m.admet?.toxicity.score ?? 0);
  const bindingEnergies = molecules.map(m => m.bindingEnergy ?? 0);
  const saScores = molecules.map(m => m.saScore ?? 5); // Default to mid-range if null
  
  const xMin = 0;
  const xMax = Math.max(1.0, ...toxicityScores);
  const yMin = Math.min(...bindingEnergies) - 10;
  const yMax = Math.max(...bindingEnergies) + 10;
  const saMin = Math.min(...saScores);
  const saMax = Math.max(...saScores);

  const xScale = (value: number) => (value - xMin) / (xMax - xMin) * innerWidth;
  const yScale = (value: number) => innerHeight - ((value - yMin) / (yMax - yMin) * innerHeight);

  // Scale radius based on SA Score. Lower score (better) = larger radius.
  const radiusScale = (value: number) => {
    const minRadius = 4;
    const maxRadius = 8;
    if (saMax === saMin) return (minRadius + maxRadius) / 2;
    // Invert the scale
    return maxRadius - ((value - saMin) / (saMax - saMin)) * (maxRadius - minRadius);
  };

  const handleMouseOver = (molecule: Molecule, e: React.MouseEvent<SVGCircleElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const svgRect = e.currentTarget.ownerSVGElement?.getBoundingClientRect(); 
    if (!svgRect) return;
    const x = rect.left - svgRect.left + rect.width / 2;
    const y = rect.top - svgRect.top - 8;
    const content = `${molecule.name}: BE=${molecule.bindingEnergy?.toFixed(2)}, Tox=${molecule.admet?.toxicity.score?.toFixed(2)}, SA=${molecule.saScore?.toFixed(2)}`;
    setTooltip({ content, x, y });
  };
  
  const handleMouseOut = () => {
    setTooltip(null);
  };

  return (
    <div className="relative">
        <svg width={width} height={height} className="font-sans text-xs">
            <g transform={`translate(${margin.left}, ${margin.top})`}>
                {/* Axes */}
                <line x1="0" y1={innerHeight} x2={innerWidth} y2={innerHeight} stroke="#6b7280" />
                <line x1="0" y1="0" x2="0" y2={innerHeight} stroke="#6b7280" />
                
                {/* X-Axis Label */}
                <text x={innerWidth / 2} y={innerHeight + 35} textAnchor="middle" fill="#a1a1aa">
                    Predicted Toxicity Score (Higher is worse)
                </text>
                
                 {/* Y-Axis Label */}
                <text transform={`rotate(-90)`} x={-innerHeight / 2} y={-35} textAnchor="middle" fill="#a1a1aa">
                    Binding Energy (kJ/mol)
                </text>

                {/* Y-Axis Ticks */}
                 {[...Array(5)].map((_, i) => {
                    const value = yMin + (i * (yMax-yMin) / 4);
                    const yPos = yScale(value);
                    return(
                    <g key={i}>
                        <line x1="-5" y1={yPos} x2="0" y2={yPos} stroke="#6b7280" />
                        <text x="-10" y={yPos + 4} textAnchor="end" fill="#a1a1aa">{value.toFixed(0)}</text>
                    </g>
                    )
                })}
                 {/* X-Axis Ticks */}
                 {[...Array(5)].map((_, i) => {
                    const value = xMin + (i * (xMax-xMin) / 4);
                    const xPos = xScale(value);
                    return(
                    <g key={i}>
                        <line x1={xPos} y1={innerHeight} x2={xPos} y2={innerHeight+5} stroke="#6b7280" />
                        <text x={xPos} y={innerHeight + 20} textAnchor="middle" fill="#a1a1aa">{value.toFixed(1)}</text>
                    </g>
                    )
                })}

                <rect x={xScale(0)} y={yScale(yMax)} width={innerWidth/4} height={innerHeight/2} fill="rgba(34, 197, 94, 0.1)" />
                <text x={5} y={15} fill="#a1a1aa" className="text-[10px] font-semibold">Optimal Quadrant</text>
                
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
                        r={isSelected ? r + 2 : r}
                        fill={isSelected ? '#3b82f6' : '#6b7280'}
                        stroke={isSelected ? '#93c5fd' : '#4b5563' }
                        strokeWidth="2"
                        className="transition-all duration-150 ease-in-out hover:scale-150 cursor-pointer"
                        onMouseOver={(e) => handleMouseOver(mol, e)}
                        onMouseOut={handleMouseOut}
                        onClick={() => onMoleculeClick(mol)}
                        />
                    );
                })}
            </g>
        </svg>
        <div className="text-center text-[10px] text-neutral-500 -mt-4">
            Point size represents Synthetic Accessibility (larger is easier to make)
        </div>
        {tooltip && (
            <div
                className="absolute bg-neutral-950 text-white text-xs px-2 py-1 rounded-md pointer-events-none transform -translate-x-1/2 -translate-y-full"
                style={{ left: tooltip.x + margin.left, top: tooltip.y + margin.top }}
            >
                {tooltip.content}
            </div>
        )}
    </div>
  );
};

export default CandidateComparisonChart;
