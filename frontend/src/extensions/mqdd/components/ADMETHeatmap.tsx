import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { Molecule } from '../types';

interface ADMETHeatmapProps {
  molecules: Molecule[];
  className?: string;
}

const ADMETHeatmap: React.FC<ADMETHeatmapProps> = ({ molecules, className }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || molecules.length === 0) return;

    const margin = { top: 40, right: 20, bottom: 40, left: 100 };
    const width = 600 - margin.left - margin.right;
    const height = (molecules.length * 40) + margin.top + margin.bottom;

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .html('') // Clear previous
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const properties = ['logP', 'logS', 'permeability', 'herg', 'toxicity', 'saScore'];
    
    // Scale for properties
    const x = d3.scaleBand()
      .range([0, width])
      .domain(properties)
      .padding(0.05);

    // Scale for molecules
    const y = d3.scaleBand()
      .range([0, molecules.length * 40])
      .domain(molecules.map(m => m.name))
      .padding(0.05);

    // Color scale - Cyan for good, Red for bad (using MQ palette)
    const color = d3.scaleSequential()
      .interpolator(d3.interpolateRgb('#ef4444', '#22d3ee'))
      .domain([0, 1]);

    // X Axis
    svg.append('g')
      .style('font-size', '10px')
      .style('font-family', 'monospace')
      .style('text-transform', 'uppercase')
      .attr('transform', `translate(0, -10)`)
      .call(d3.axisTop(x).tickSize(0))
      .select('.domain').remove();

    // Y Axis
    svg.append('g')
      .style('font-size', '11px')
      .style('font-family', 'Inter, sans-serif')
      .call(d3.axisLeft(y).tickSize(0))
      .select('.domain').remove();

    // Cells
    molecules.forEach((mol) => {
      properties.forEach(prop => {
        let val = 0;
        if (prop === 'saScore') {
            val = (mol.saScore || 0) / 10; // Normalize 0-10 to 0-1
        } else {
            const admet = mol.admet as any;
            val = admet && admet[prop] ? (admet[prop].score || 0.5) : 0.5;
        }

        svg.append('rect')
          .attr('x', x(prop)!)
          .attr('y', y(mol.name)!)
          .attr('rx', 4)
          .attr('ry', 4)
          .attr('width', x.bandwidth())
          .attr('height', y.bandwidth())
          .style('fill', color(val))
          .style('stroke-width', 2)
          .style('stroke', 'rgba(255,255,255,0.05)')
          .style('opacity', 0.8)
          .on('mouseover', function() {
            d3.select(this).style('opacity', 1).style('stroke', '#fff');
          })
          .on('mouseleave', function() {
            d3.select(this).style('opacity', 0.8).style('stroke', 'rgba(255,255,255,0.05)');
          });

        // Value text
        svg.append('text')
          .attr('x', x(prop)! + x.bandwidth() / 2)
          .attr('y', y(mol.name)! + y.bandwidth() / 2)
          .attr('dy', '.35em')
          .attr('text-anchor', 'middle')
          .style('font-size', '10px')
          .style('font-weight', 'bold')
          .style('fill', '#000')
          .style('pointer-events', 'none')
          .text(val.toFixed(2));
      });
    });

  }, [molecules]);

  return (
    <div className={`overflow-x-auto ${className}`}>
      <svg ref={svgRef} className="mx-auto" />
    </div>
  );
};

export default ADMETHeatmap;
