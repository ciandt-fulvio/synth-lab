// frontend/src/components/experiments/results/charts/SankeyDiagram.tsx
// Custom Sankey diagram with explicit level positioning

import { useMemo, useState } from 'react';
import type { SankeyChart as SankeyData } from '@/types/simulation';

interface SankeyDiagramProps {
  data: SankeyData;
}

// Node colors by ID
const NODE_COLORS: Record<string, string> = {
  all: '#475569', // Slate-600 - neutral starting point
  attempted: '#8b5cf6', // Violet - attempted
  not_attempted: '#f59e0b', // Amber/Gold - didn't try
  success: '#22c55e', // Green - succeeded
  failed: '#ef4444', // Red - failed
};

// Node labels for legend
const NODE_LABELS: Record<string, string> = {
  all: 'Todos',
  attempted: 'Tentaram',
  not_attempted: 'Não Tentaram',
  success: 'Sucesso',
  failed: 'Falharam',
};

// Explicit depth/level for each node
const NODE_DEPTHS: Record<string, number> = {
  all: 0,
  attempted: 1,
  not_attempted: 1, // Same level as "attempted"
  success: 2,
  failed: 2,
};

interface ComputedNode {
  id: string;
  label: string;
  value: number;
  depth: number;
  x: number;
  y: number;
  height: number;
  color: string;
}

interface ComputedLink {
  source: string;
  target: string;
  value: number;
  sourceNode: ComputedNode;
  targetNode: ComputedNode;
  sourceY: number;
  targetY: number;
  thickness: number;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  content: string;
}

export function SankeyDiagram({ data }: SankeyDiagramProps) {
  const { nodes, links, total_synths } = data;
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, x: 0, y: 0, content: '' });

  // Chart dimensions
  const width = 600;
  const height = 350;
  const margin = { top: 20, right: 150, bottom: 20, left: 20 };
  const nodeWidth = 12;
  const nodePadding = 30;

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Compute node and link positions
  const { computedNodes, computedLinks } = useMemo(() => {
    // Filter out zero-value nodes and links
    const validLinks = links.filter((l) => l.value > 0);
    const usedNodeIds = new Set<string>();
    validLinks.forEach((l) => {
      usedNodeIds.add(l.source);
      usedNodeIds.add(l.target);
    });
    const validNodes = nodes.filter((n) => usedNodeIds.has(n.id));

    if (validNodes.length === 0) {
      return { computedNodes: [], computedLinks: [] };
    }

    // Group nodes by depth
    const nodesByDepth: Record<number, typeof validNodes> = {};
    validNodes.forEach((node) => {
      const depth = NODE_DEPTHS[node.id] ?? 0;
      if (!nodesByDepth[depth]) nodesByDepth[depth] = [];
      nodesByDepth[depth].push(node);
    });

    const maxDepth = Math.max(...Object.keys(nodesByDepth).map(Number));
    const depthWidth = innerWidth / (maxDepth + 1);

    // Find max total value (usually at depth 0) for proportional scaling
    const maxTotalValue = Math.max(
      ...Object.values(nodesByDepth).map((nodes) =>
        nodes.reduce((sum, n) => sum + n.value, 0)
      )
    );

    // Calculate node positions
    const computedNodesMap: Record<string, ComputedNode> = {};

    Object.entries(nodesByDepth).forEach(([depthStr, depthNodes]) => {
      const depth = Number(depthStr);
      const x = margin.left + depth * depthWidth;

      // Calculate heights proportional to absolute values (relative to max total)
      const totalValueAtDepth = depthNodes.reduce((sum, n) => sum + n.value, 0);
      const totalPaddingNeeded = (depthNodes.length - 1) * nodePadding;

      // Scale factor: available height for this depth's total value
      const availableForValues = innerHeight - totalPaddingNeeded;
      const heightPerUnit = availableForValues / maxTotalValue;

      // Center vertically if total is less than max
      const totalNodesHeight = totalValueAtDepth * heightPerUnit;
      const startY = margin.top + (innerHeight - totalNodesHeight - totalPaddingNeeded) / 2;

      let currentY = startY;
      depthNodes.forEach((node) => {
        const nodeHeight = Math.max(15, node.value * heightPerUnit);
        computedNodesMap[node.id] = {
          id: node.id,
          label: node.label,
          value: node.value,
          depth,
          x,
          y: currentY,
          height: nodeHeight,
          color: NODE_COLORS[node.id] || '#94a3b8',
        };
        currentY += nodeHeight + nodePadding;
      });
    });

    // Track cumulative offsets for links at each node
    const sourceOffsets: Record<string, number> = {};
    const targetOffsets: Record<string, number> = {};

    // Calculate link positions
    const computedLinksList: ComputedLink[] = validLinks.map((link) => {
      const sourceNode = computedNodesMap[link.source];
      const targetNode = computedNodesMap[link.target];

      if (!sourceNode || !targetNode) {
        return null;
      }

      // Initialize offsets
      if (sourceOffsets[link.source] === undefined) sourceOffsets[link.source] = 0;
      if (targetOffsets[link.target] === undefined) targetOffsets[link.target] = 0;

      // Calculate link thickness proportional to value
      const thickness = Math.max(2, (link.value / sourceNode.value) * sourceNode.height);

      // Calculate Y positions with offsets
      const sourceY = sourceNode.y + sourceOffsets[link.source] + thickness / 2;
      const targetY = targetNode.y + targetOffsets[link.target] + thickness / 2;

      // Update offsets
      sourceOffsets[link.source] += thickness;
      targetOffsets[link.target] += thickness;

      return {
        source: link.source,
        target: link.target,
        value: link.value,
        sourceNode,
        targetNode,
        sourceY,
        targetY,
        thickness,
      };
    }).filter((l): l is ComputedLink => l !== null);

    return {
      computedNodes: Object.values(computedNodesMap),
      computedLinks: computedLinksList,
    };
  }, [nodes, links, innerWidth, innerHeight, margin.left, margin.top]);

  // Generate curved path for links
  const getLinkPath = (link: ComputedLink) => {
    const sourceX = link.sourceNode.x + nodeWidth;
    const targetX = link.targetNode.x;
    const controlOffset = (targetX - sourceX) * 0.5;

    return `
      M ${sourceX},${link.sourceY - link.thickness / 2}
      C ${sourceX + controlOffset},${link.sourceY - link.thickness / 2}
        ${targetX - controlOffset},${link.targetY - link.thickness / 2}
        ${targetX},${link.targetY - link.thickness / 2}
      L ${targetX},${link.targetY + link.thickness / 2}
      C ${targetX - controlOffset},${link.targetY + link.thickness / 2}
        ${sourceX + controlOffset},${link.sourceY + link.thickness / 2}
        ${sourceX},${link.sourceY + link.thickness / 2}
      Z
    `;
  };

  const handleMouseMove = (e: React.MouseEvent, content: string) => {
    const rect = e.currentTarget.closest('svg')?.getBoundingClientRect();
    if (rect) {
      setTooltip({
        visible: true,
        x: e.clientX - rect.left + 10,
        y: e.clientY - rect.top - 10,
        content,
      });
    }
  };

  const handleMouseLeave = () => {
    setTooltip({ ...tooltip, visible: false });
  };

  if (computedNodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-500">
        <p className="text-sm">Dados insuficientes para o diagrama Sankey</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap gap-4 justify-center">
        {Object.entries(NODE_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: color }}
            />
            <span className="text-sm text-slate-600">
              {NODE_LABELS[key] || key}
            </span>
          </div>
        ))}
      </div>

      {/* Sankey diagram */}
      <div className="w-full overflow-x-auto">
        <svg width={width} height={height} className="mx-auto">
          {/* Links */}
          <g>
            {computedLinks.map((link, i) => (
              <path
                key={`link-${i}`}
                d={getLinkPath(link)}
                fill={NODE_COLORS[link.source] || '#94a3b8'}
                fillOpacity={0.3}
                stroke={NODE_COLORS[link.source] || '#94a3b8'}
                strokeWidth={0.5}
                strokeOpacity={0.5}
                className="cursor-pointer transition-opacity hover:fill-opacity-50"
                onMouseMove={(e) =>
                  handleMouseMove(e, `${link.sourceNode.label} → ${link.targetNode.label}: ${link.value} synths`)
                }
                onMouseLeave={handleMouseLeave}
              />
            ))}
          </g>

          {/* Nodes */}
          <g>
            {computedNodes.map((node) => (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={nodeWidth}
                  height={node.height}
                  fill={node.color}
                  rx={3}
                  ry={3}
                  className="cursor-pointer"
                  onMouseMove={(e) => handleMouseMove(e, `${node.label}: ${node.value} synths`)}
                  onMouseLeave={handleMouseLeave}
                />
                {/* Node label */}
                <text
                  x={node.x + nodeWidth + 8}
                  y={node.y + node.height / 2}
                  dominantBaseline="middle"
                  className="text-xs font-medium fill-slate-700 pointer-events-none"
                >
                  {node.label}
                </text>
                <text
                  x={node.x + nodeWidth + 8}
                  y={node.y + node.height / 2 + 14}
                  dominantBaseline="middle"
                  className="text-xs fill-slate-500 pointer-events-none"
                >
                  {node.value}
                </text>
              </g>
            ))}
          </g>

          {/* Tooltip */}
          {tooltip.visible && (
            <g transform={`translate(${tooltip.x}, ${tooltip.y})`}>
              <rect
                x={0}
                y={-30}
                width={tooltip.content.length * 6 + 20}
                height={28}
                fill="white"
                stroke="#e2e8f0"
                strokeWidth={1}
                rx={6}
                ry={6}
                filter="drop-shadow(0 2px 4px rgba(0,0,0,0.1))"
              />
              <text
                x={10}
                y={-12}
                className="text-xs fill-slate-700"
              >
                {tooltip.content}
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Summary */}
      <p className="text-center text-sm text-slate-500">
        Fluxo de {total_synths} synths na jornada
      </p>
    </div>
  );
}
