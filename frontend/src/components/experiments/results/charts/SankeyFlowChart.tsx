// frontend/src/components/experiments/results/charts/SankeyFlowChart.tsx
// Sankey diagram showing outcome flow from population to root causes

import { useRef, useEffect } from 'react';
import * as d3 from 'd3-selection';
import { sankey, sankeyLinkHorizontal, SankeyNode, SankeyLink } from 'd3-sankey';
import type { SankeyFlowChart as SankeyFlowData } from '@/types/simulation';

interface SankeyFlowChartProps {
  data: SankeyFlowData;
}

// D3-Sankey node and link types
interface D3SankeyNode {
  id: string;
  label: string;
  level: 1 | 2 | 3;
  color: string;
  value: number;
  x0?: number;
  x1?: number;
  y0?: number;
  y1?: number;
}

interface D3SankeyLink {
  source: string | D3SankeyNode;
  target: string | D3SankeyNode;
  value: number;
  width?: number;
  y0?: number;
  y1?: number;
}

export function SankeyFlowChart({ data }: SankeyFlowChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 700;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Prepare data for d3-sankey
    // Using nodeId() means source/target should be string IDs
    const nodes: D3SankeyNode[] = data.nodes.map((node) => ({
      ...node,
    }));

    const links: D3SankeyLink[] = data.links.map((link) => ({
      source: link.source,  // Keep as string ID - d3-sankey will resolve via nodeId()
      target: link.target,  // Keep as string ID - d3-sankey will resolve via nodeId()
      value: link.value,
    }));

    // Create sankey generator
    const sankeyGenerator = sankey<D3SankeyNode, D3SankeyLink>()
      .nodeId((d) => d.id)
      .nodeWidth(20)
      .nodePadding(30)
      .extent([
        [margin.left, margin.top],
        [innerWidth, innerHeight],
      ]);

    // Generate layout
    const { nodes: layoutNodes, links: layoutLinks } = sankeyGenerator({
      nodes: nodes.map((n) => ({ ...n })),
      links: links.map((l) => ({ ...l })),
    });

    const g = svg.append('g');

    // Draw links (flows)
    g.append('g')
      .attr('fill', 'none')
      .selectAll('path')
      .data(layoutLinks)
      .join('path')
      .attr('d', sankeyLinkHorizontal())
      .attr('stroke', (d) => {
        const sourceNode = d.source as SankeyNode<D3SankeyNode, D3SankeyLink>;
        return (sourceNode as D3SankeyNode).color || '#cbd5e1';
      })
      .attr('stroke-opacity', 0.5)
      .attr('stroke-width', (d) => Math.max(1, d.width || 0))
      .append('title')
      .text((d) => {
        const sourceNode = d.source as SankeyNode<D3SankeyNode, D3SankeyLink>;
        const targetNode = d.target as SankeyNode<D3SankeyNode, D3SankeyLink>;
        return `${(sourceNode as D3SankeyNode).label} → ${(targetNode as D3SankeyNode).label}: ${d.value} synths`;
      });

    // Draw nodes
    const nodeGroup = g
      .append('g')
      .selectAll('g')
      .data(layoutNodes)
      .join('g')
      .attr('transform', (d) => `translate(${d.x0},${d.y0})`);

    // Node rectangles
    nodeGroup
      .append('rect')
      .attr('height', (d) => (d.y1 || 0) - (d.y0 || 0))
      .attr('width', (d) => (d.x1 || 0) - (d.x0 || 0))
      .attr('fill', (d) => d.color)
      .attr('rx', 4)
      .attr('ry', 4);

    // Node labels
    nodeGroup
      .append('text')
      .attr('x', (d) => {
        const nodeWidth = (d.x1 || 0) - (d.x0 || 0);
        // Level 1 (population) - label on right
        if (d.level === 1) return nodeWidth + 6;
        // Level 3 (root causes) - label on right
        if (d.level === 3) return nodeWidth + 6;
        // Level 2 (outcomes) - label on right
        return nodeWidth + 6;
      })
      .attr('y', (d) => ((d.y1 || 0) - (d.y0 || 0)) / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'start')
      .attr('fill', '#334155')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .text((d) => d.label);

    // Value labels inside nodes
    nodeGroup
      .append('text')
      .attr('x', (d) => ((d.x1 || 0) - (d.x0 || 0)) / 2)
      .attr('y', (d) => ((d.y1 || 0) - (d.y0 || 0)) / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .text((d) => d.value);
  }, [data]);

  if (!data.nodes.length) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        Sem dados para exibir
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Summary stats */}
      <div className="flex items-center justify-between mb-4 text-sm text-slate-600">
        <div>
          Total: <span className="font-medium text-slate-800">{data.total_synths}</span> synths
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: '#f59e0b' }}
            />
            <span>Não tentou: {data.outcome_counts.did_not_try}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: '#ef4444' }}
            />
            <span>Falhou: {data.outcome_counts.failed}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: '#22c55e' }}
            />
            <span>Sucesso: {data.outcome_counts.success}</span>
          </div>
        </div>
      </div>

      {/* Sankey diagram */}
      <svg
        ref={svgRef}
        viewBox="0 0 700 400"
        className="w-full h-auto"
        style={{ maxHeight: '400px' }}
      />
    </div>
  );
}
