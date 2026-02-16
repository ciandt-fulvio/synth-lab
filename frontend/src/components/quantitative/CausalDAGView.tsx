/**
 * CausalDAGView component.
 *
 * SVG-based visualization of the causal DAG with 3-layer layout:
 * - Left: demographic root nodes
 * - Center: mediator nodes
 * - Right: outcome node
 *
 * Nodes are rounded rectangles with multi-line text (up to 3 lines).
 * Edges: quadratic bezier curves. Stroke width AND color vary by mu
 * (lighter blue = weak, darker blue = strong).
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

const SVG_WIDTH = 820;
const SVG_HEIGHT = 420;
const NODE_W = 110;
const NODE_H = 52;
const NODE_RX = 10;
const LAYER_X = [80, 410, 740]; // x positions for 3 layers

/** Blue shades by mu intensity: 0 (weak) → 4 (strong). */
const EDGE_COLORS = ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1e40af'];
const ACTIVE_COLOR = '#1e3a8a';

function muToColorIndex(mu: number): number {
  return Math.min(Math.floor(mu * EDGE_COLORS.length), EDGE_COLORS.length - 1);
}

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

/** Break label into lines of up to maxChars, max 3 lines. */
function wrapLabel(label: string, maxChars = 13): string[] {
  const words = label.split(/\s+/);
  const lines: string[] = [];
  let current = '';

  for (const word of words) {
    if (lines.length >= 3) break;
    const test = current ? `${current} ${word}` : word;
    if (test.length <= maxChars || !current) {
      current = test;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current && lines.length < 3) {
    lines.push(current);
  }
  // Truncate last line if overflow
  const last = lines.length - 1;
  if (last >= 0 && lines[last].length > maxChars) {
    lines[last] = lines[last].slice(0, maxChars - 1) + '\u2026';
  }

  return lines;
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
        style={{ maxHeight: '440px' }}
      >
        <defs>
          {/* One arrow marker per color tier + active */}
          {EDGE_COLORS.map((color, i) => (
            <marker
              key={`arrow-${i}`}
              id={`arrow-${i}`}
              viewBox="0 0 10 6"
              refX="10"
              refY="3"
              markerWidth="8"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 3 L 0 6 z" fill={color} />
            </marker>
          ))}
          <marker
            id="arrow-active"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 z" fill={ACTIVE_COLOR} />
          </marker>
        </defs>

        {/* Edges */}
        {model.edges.map((edge) => {
          const from = nodePositions.get(edge.from_node);
          const to = nodePositions.get(edge.to_node);
          if (!from || !to) return null;

          const isActive = activeEdgeId === edge.id;
          const selectedMu = edge.selected_option !== null
            ? edge.options[edge.selected_option!].mu
            : edge.options[edge.default_option].mu;

          const colorIdx = muToColorIndex(selectedMu);
          const color = isActive ? ACTIVE_COLOR : EDGE_COLORS[colorIdx];
          const strokeWidth = 1.5 + selectedMu * 3.5;
          const opacity = isActive ? 1 : 0.85;
          const markerEnd = isActive ? 'url(#arrow-active)' : `url(#arrow-${colorIdx})`;

          // Connect right edge of source → left edge of target
          const fromX = from.x + NODE_W / 2;
          const fromY = from.y;
          const toX = to.x - NODE_W / 2;
          const toY = to.y;

          // Quadratic bezier: control point midway-x, midway-y offset
          const midX = (fromX + toX) / 2;
          const midY = (fromY + toY) / 2;
          const offsetY = (fromY - toY) * 0.25;
          const cx = midX;
          const cy = midY - offsetY;

          return (
            <g
              key={edge.id}
              className="cursor-pointer"
              onClick={() => onEdgeClick?.(edge.id)}
            >
              {/* Hit area (invisible wider path for easier clicking) */}
              <path
                d={`M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`}
                fill="none"
                stroke="transparent"
                strokeWidth={Math.max(strokeWidth + 8, 12)}
              />
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
          const fills = ['#f1f5f9', '#f5f3ff', '#ecfdf5']; // slate-100, violet-50, emerald-50
          const strokes = ['#cbd5e1', '#c4b5fd', '#6ee7b7']; // slate-300, violet-300, emerald-300
          const textFills = ['#334155', '#5b21b6', '#047857']; // slate-700, violet-800, emerald-700

          const lines = wrapLabel(node);
          const lineHeight = 14;
          const textBlockHeight = lines.length * lineHeight;
          const startY = pos.y - textBlockHeight / 2 + lineHeight / 2;

          return (
            <g key={node}>
              <rect
                x={pos.x - NODE_W / 2}
                y={pos.y - NODE_H / 2}
                width={NODE_W}
                height={NODE_H}
                rx={NODE_RX}
                ry={NODE_RX}
                fill={fills[layer]}
                stroke={strokes[layer]}
                strokeWidth={1.5}
              />
              <text
                x={pos.x}
                textAnchor="middle"
                fill={textFills[layer]}
                className="text-[11.5px] font-medium pointer-events-none"
              >
                {lines.map((line, i) => (
                  <tspan key={i} x={pos.x} y={startY + i * lineHeight}>
                    {line}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })}

      </svg>
    </div>
  );
}
