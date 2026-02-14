/**
 * CausalDAGView component.
 *
 * SVG-based visualization of the causal DAG with 3-layer layout:
 * - Left: demographic root nodes
 * - Center: mediator nodes
 * - Right: outcome node
 *
 * Edges rendered as quadratic bezier curves.
 * Stroke width proportional to mu. Color: blue (direction=1), orange (direction=-1).
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Spec: specs/042-quantitative-analysis/spec.md
 */

import { useMemo } from 'react';
import type { CausalModel, CausalEdge } from '@/types/quantitative-analysis';

interface CausalDAGViewProps {
  model: CausalModel;
  activeEdgeId?: string | null;
  onEdgeClick?: (edgeId: string) => void;
}

interface NodePosition {
  x: number;
  y: number;
  label: string;
  layer: number;
}

/**
 * Classify nodes into 3 layers based on edge topology.
 *
 * Layer 0 (left): nodes that only appear as "from" (roots/demographics)
 * Layer 2 (right): nodes that only appear as "to" (outcome)
 * Layer 1 (center): everything else (mediators)
 */
function classifyNodes(
  nodes: string[],
  edges: CausalEdge[]
): Map<string, number> {
  const fromNodes = new Set(edges.map((e) => e.from_node));
  const toNodes = new Set(edges.map((e) => e.to_node));

  const layerMap = new Map<string, number>();

  for (const node of nodes) {
    const isFrom = fromNodes.has(node);
    const isTo = toNodes.has(node);

    if (isFrom && !isTo) {
      layerMap.set(node, 0); // root / demographic
    } else if (isTo && !isFrom) {
      layerMap.set(node, 2); // outcome
    } else {
      layerMap.set(node, 1); // mediator
    }
  }

  return layerMap;
}

const SVG_WIDTH = 700;
const SVG_HEIGHT = 400;
const NODE_RADIUS = 28;
const LAYER_X = [100, 350, 600]; // x positions for 3 layers

function layoutNodes(
  nodes: string[],
  layerMap: Map<string, number>
): Map<string, NodePosition> {
  const layers: string[][] = [[], [], []];
  for (const node of nodes) {
    const layer = layerMap.get(node) ?? 1;
    layers[layer].push(node);
  }

  const positions = new Map<string, NodePosition>();

  for (let layer = 0; layer < 3; layer++) {
    const nodesInLayer = layers[layer];
    const count = nodesInLayer.length;
    const spacing = SVG_HEIGHT / (count + 1);

    nodesInLayer.forEach((node, idx) => {
      positions.set(node, {
        x: LAYER_X[layer],
        y: spacing * (idx + 1),
        label: node,
        layer,
      });
    });
  }

  return positions;
}

function truncateLabel(label: string, maxLen = 14): string {
  return label.length > maxLen ? `${label.slice(0, maxLen - 1)}...` : label;
}

export function CausalDAGView({ model, activeEdgeId, onEdgeClick }: CausalDAGViewProps) {
  const { nodePositions, layerMap } = useMemo(() => {
    const lm = classifyNodes(model.nodes, model.edges);
    const np = layoutNodes(model.nodes, lm);
    return { nodePositions: np, layerMap: lm };
  }, [model.nodes, model.edges]);

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="w-full h-auto min-w-[500px]"
        style={{ maxHeight: '420px' }}
      >
        <defs>
          <marker
            id="arrowBlue"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 z" fill="#3b82f6" />
          </marker>
          <marker
            id="arrowOrange"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 z" fill="#f59e0b" />
          </marker>
          <marker
            id="arrowBlueActive"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 z" fill="#1d4ed8" />
          </marker>
          <marker
            id="arrowOrangeActive"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 z" fill="#d97706" />
          </marker>
        </defs>

        {/* Edges */}
        {model.edges.map((edge) => {
          const from = nodePositions.get(edge.from_node);
          const to = nodePositions.get(edge.to_node);
          if (!from || !to) return null;

          const isActive = activeEdgeId === edge.id;
          const isAnswered = edge.selected_option !== null;
          const selectedMu = isAnswered
            ? edge.options[edge.selected_option!].mu
            : edge.options[edge.default_option].mu;
          const strokeWidth = 1.5 + selectedMu * 3.5;
          const baseColor = edge.direction === 1 ? '#3b82f6' : '#f59e0b';
          const activeColor = edge.direction === 1 ? '#1d4ed8' : '#d97706';
          const color = isActive ? activeColor : baseColor;
          const opacity = isActive ? 1 : isAnswered ? 0.85 : 0.5;
          const markerEnd = isActive
            ? edge.direction === 1
              ? 'url(#arrowBlueActive)'
              : 'url(#arrowOrangeActive)'
            : edge.direction === 1
              ? 'url(#arrowBlue)'
              : 'url(#arrowOrange)';

          // Quadratic bezier: control point midway-x, midway-y offset
          const midX = (from.x + to.x) / 2;
          const midY = (from.y + to.y) / 2;
          const offsetY = (from.y - to.y) * 0.3;
          const cx = midX;
          const cy = midY - offsetY;

          // Shorten path to stop at node edge
          const dx = to.x - cx;
          const dy = to.y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const toX = to.x - (dx / dist) * (NODE_RADIUS + 6);
          const toY = to.y - (dy / dist) * (NODE_RADIUS + 6);

          const dxStart = cx - from.x;
          const dyStart = cy - from.y;
          const distStart = Math.sqrt(dxStart * dxStart + dyStart * dyStart);
          const fromX = from.x + (dxStart / distStart) * (NODE_RADIUS + 2);
          const fromY = from.y + (dyStart / distStart) * (NODE_RADIUS + 2);

          return (
            <g
              key={edge.id}
              className="cursor-pointer"
              onClick={() => onEdgeClick?.(edge.id)}
            >
              <path
                d={`M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                opacity={opacity}
                markerEnd={markerEnd}
                className="transition-all duration-200"
              />
              {isActive && (
                <path
                  d={`M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`}
                  fill="none"
                  stroke={color}
                  strokeWidth={strokeWidth + 4}
                  opacity={0.15}
                />
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {model.nodes.map((node) => {
          const pos = nodePositions.get(node);
          if (!pos) return null;

          const layer = layerMap.get(node) ?? 1;
          const bgColors = [
            'fill-slate-100 stroke-slate-300',
            'fill-violet-50 stroke-violet-300',
            'fill-emerald-50 stroke-emerald-300',
          ];
          const textColors = ['text-slate-700', 'text-violet-700', 'text-emerald-700'];

          return (
            <g key={node}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={NODE_RADIUS}
                className={bgColors[layer]}
                strokeWidth={1.5}
              />
              <text
                x={pos.x}
                y={pos.y}
                textAnchor="middle"
                dominantBaseline="central"
                className={`text-[10px] font-medium ${textColors[layer]} pointer-events-none`}
              >
                {truncateLabel(node)}
              </text>
            </g>
          );
        })}

        {/* Legend */}
        <g transform="translate(10, 375)">
          <line x1="0" y1="0" x2="20" y2="0" stroke="#3b82f6" strokeWidth="2" />
          <text x="24" y="4" className="text-[9px] fill-slate-500">Positivo (+)</text>
          <line x1="100" y1="0" x2="120" y2="0" stroke="#f59e0b" strokeWidth="2" />
          <text x="124" y="4" className="text-[9px] fill-slate-500">Negativo (-)</text>
        </g>
      </svg>
    </div>
  );
}
