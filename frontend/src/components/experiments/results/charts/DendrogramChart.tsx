// frontend/src/components/experiments/results/charts/DendrogramChart.tsx
// Dendrogram visualization for hierarchical clustering

import { useState } from 'react';
import type { HierarchicalResult } from '@/types/simulation';

interface DendrogramChartProps {
  data: HierarchicalResult;
  onCutHeight?: (height: number) => void;
}

interface DendrogramNode {
  id: string;
  children?: DendrogramNode[];
  height: number;
  count: number;
}

// Recursive component to render dendrogram branches
interface BranchProps {
  node: DendrogramNode;
  x: number;
  y: number;
  width: number;
  heightScale: (h: number) => number;
  cutHeight?: number;
  onNodeClick?: (node: DendrogramNode) => void;
}

function Branch({ node, x, y, width, heightScale, cutHeight, onNodeClick }: BranchProps) {
  const nodeY = heightScale(node.height);
  const isCut = cutHeight !== undefined && node.height > cutHeight;

  if (!node.children || node.children.length === 0) {
    // Leaf node
    return (
      <g>
        <line
          x1={x}
          y1={y}
          x2={x}
          y2={nodeY}
          stroke={isCut ? '#94a3b8' : '#6366f1'}
          strokeWidth={2}
        />
        <circle
          cx={x}
          cy={nodeY}
          r={4}
          fill={isCut ? '#94a3b8' : '#6366f1'}
          className="cursor-pointer hover:fill-violet-600"
          onClick={() => onNodeClick?.(node)}
        />
        <text
          x={x}
          y={nodeY + 15}
          textAnchor="middle"
          fontSize={8}
          fill="#64748b"
        >
          {node.count}
        </text>
      </g>
    );
  }

  // Internal node with children
  const childWidth = width / node.children.length;
  const childXs = node.children.map((_, i) => x - width / 2 + childWidth / 2 + i * childWidth);

  return (
    <g>
      {/* Vertical line from parent */}
      <line
        x1={x}
        y1={y}
        x2={x}
        y2={nodeY}
        stroke={isCut ? '#94a3b8' : '#6366f1'}
        strokeWidth={2}
      />

      {/* Horizontal line connecting children */}
      <line
        x1={childXs[0]}
        y1={nodeY}
        x2={childXs[childXs.length - 1]}
        y2={nodeY}
        stroke={isCut ? '#94a3b8' : '#6366f1'}
        strokeWidth={2}
      />

      {/* Node marker */}
      <circle
        cx={x}
        cy={nodeY}
        r={3}
        fill={isCut ? '#94a3b8' : '#6366f1'}
        className="cursor-pointer hover:fill-violet-600"
        onClick={() => onNodeClick?.(node)}
      />

      {/* Cut line indicator */}
      {cutHeight !== undefined && Math.abs(node.height - cutHeight) < 0.01 && (
        <line
          x1={x - width / 2 - 10}
          y1={nodeY}
          x2={x + width / 2 + 10}
          y2={nodeY}
          stroke="#ef4444"
          strokeWidth={2}
          strokeDasharray="4 4"
        />
      )}

      {/* Render children */}
      {node.children.map((child, i) => (
        <Branch
          key={child.id}
          node={child}
          x={childXs[i]}
          y={nodeY}
          width={childWidth}
          heightScale={heightScale}
          cutHeight={cutHeight}
          onNodeClick={onNodeClick}
        />
      ))}
    </g>
  );
}

export function DendrogramChart({ data, onCutHeight }: DendrogramChartProps) {
  const [selectedHeight, setSelectedHeight] = useState<number | null>(null);

  const { dendrogram_tree, cut_height, n_clusters, total_synths } = data;

  // Parse dendrogram tree if it's a string
  const tree: DendrogramNode = typeof dendrogram_tree === 'string'
    ? JSON.parse(dendrogram_tree)
    : dendrogram_tree;

  // Find max height for scaling
  const findMaxHeight = (node: DendrogramNode): number => {
    if (!node.children || node.children.length === 0) return node.height;
    return Math.max(node.height, ...node.children.map(findMaxHeight));
  };

  const maxHeight = findMaxHeight(tree);
  const svgHeight = 350;
  const svgWidth = 600;
  const margin = { top: 30, bottom: 40, left: 60, right: 20 };
  const plotHeight = svgHeight - margin.top - margin.bottom;
  const plotWidth = svgWidth - margin.left - margin.right;

  // Height scale (inverted - higher values at top)
  const heightScale = (h: number) =>
    margin.top + plotHeight - (h / maxHeight) * plotHeight;

  const handleNodeClick = (node: DendrogramNode) => {
    setSelectedHeight(node.height);
    onCutHeight?.(node.height);
  };

  return (
    <div className="space-y-4">
      {/* SVG Dendrogram */}
      <div className="flex justify-center overflow-x-auto">
        <svg width={svgWidth} height={svgHeight} className="bg-slate-50 rounded-lg">
          {/* Y-axis (height) */}
          <g>
            {[0, 0.25, 0.5, 0.75, 1].map((t) => {
              const h = t * maxHeight;
              const y = heightScale(h);
              return (
                <g key={t}>
                  <line
                    x1={margin.left - 5}
                    y1={y}
                    x2={margin.left}
                    y2={y}
                    stroke="#94a3b8"
                  />
                  <text
                    x={margin.left - 10}
                    y={y}
                    textAnchor="end"
                    dominantBaseline="middle"
                    fontSize={10}
                    fill="#64748b"
                  >
                    {h.toFixed(2)}
                  </text>
                </g>
              );
            })}
            <text
              x={15}
              y={svgHeight / 2}
              textAnchor="middle"
              fontSize={12}
              fill="#64748b"
              transform={`rotate(-90, 15, ${svgHeight / 2})`}
            >
              Distância
            </text>
          </g>

          {/* Dendrogram tree */}
          <g transform={`translate(${margin.left + plotWidth / 2}, 0)`}>
            <Branch
              node={tree}
              x={0}
              y={margin.top}
              width={plotWidth * 0.9}
              heightScale={heightScale}
              cutHeight={cut_height}
              onNodeClick={handleNodeClick}
            />
          </g>

          {/* Cut line */}
          {cut_height && (
            <line
              x1={margin.left}
              y1={heightScale(cut_height)}
              x2={svgWidth - margin.right}
              y2={heightScale(cut_height)}
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="6 3"
            />
          )}
        </svg>
      </div>

      {/* Cluster info */}
      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-indigo-500" />
          <span className="text-slate-600">
            {n_clusters} clusters ({total_synths} synths)
          </span>
        </div>
        {cut_height && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-red-500" style={{ borderStyle: 'dashed' }} />
            <span className="text-slate-600">
              Corte em h={cut_height.toFixed(2)}
            </span>
          </div>
        )}
      </div>

      {/* Instructions */}
      <p className="text-center text-xs text-slate-500">
        Clique em um nó para definir a altura de corte e criar clusters
      </p>
    </div>
  );
}
