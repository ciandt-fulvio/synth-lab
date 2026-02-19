/**
 * CausalDAGView component.
 *
 * SVG-based visualization of the causal DAG with 3-layer layout:
 * - Left: demographic root nodes
 * - Center: mediator nodes
 * - Right: outcome node
 *
 * Nodes are rounded rectangles with multi-line text (up to 3 lines).
 * Edges:
 *   - Cross-layer (causal): solid blue bezier curves, width varies by mu
 *   - Same-layer (correlational, between mediators): dashed violet, fixed width
 *
 * Node ordering uses a barycenter heuristic to minimize edge crossings:
 *   1. Layer 1 nodes sorted by average position of their layer-0 sources
 *   2. Layer 0 nodes sorted by average position of their layer-1 targets
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

const SVG_WIDTH = 1100;
const SVG_HEIGHT = 580;
const NODE_W = 110;
const NODE_H = 68;
const NODE_RX = 10;
const LAYER_X = [100, 520, 1000]; // x positions for 3 layers

/** Blue shades by mu intensity: 0 (weak) → 4 (strong). */
const EDGE_COLORS = ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1e40af'];
const ACTIVE_COLOR = '#1e3a8a';

function muToColorIndex(mu: number): number {
  return Math.min(Math.floor(mu * EDGE_COLORS.length), EDGE_COLORS.length - 1);
}

/**
 * Layout nodes within each layer using a barycenter heuristic to reduce
 * edge crossings between layer 0 and layer 1.
 *
 * Steps:
 * 1. Give layer 1 initial positional indices.
 * 2. Sort layer 0 nodes by average index of their layer-1 targets (barycenter).
 * 3. Re-index layer 0, then sort layer 1 nodes by average index of their layer-0 sources.
 * 4. Assign final y positions from SVG_HEIGHT / (count + 1) spacing.
 */
function layoutNodes(
  nodes: string[],
  edges: CausalEdge[],
  layerMap: Map<string, number>
): Map<string, NodePosition> {
  const layers: string[][] = [[], [], []];
  for (const node of nodes) {
    const layer = layerMap.get(node) ?? 1;
    layers[layer].push(node);
  }

  // Step 1: initial index for layer 1
  const layer1InitPos = new Map<string, number>();
  layers[1].forEach((n, i) => layer1InitPos.set(n, i));

  // Step 2: sort layer 0 by barycenter toward layer 1
  layers[0].sort((a, b) => {
    const aTargets = edges
      .filter((e) => e.from_node === a && layerMap.get(e.to_node) === 1)
      .map((e) => layer1InitPos.get(e.to_node) ?? 0);
    const bTargets = edges
      .filter((e) => e.from_node === b && layerMap.get(e.to_node) === 1)
      .map((e) => layer1InitPos.get(e.to_node) ?? 0);
    const aAvg = aTargets.length
      ? aTargets.reduce((x, y) => x + y, 0) / aTargets.length
      : 0;
    const bAvg = bTargets.length
      ? bTargets.reduce((x, y) => x + y, 0) / bTargets.length
      : 0;
    return aAvg - bAvg;
  });

  // Step 3: re-index layer 0, then sort layer 1 by barycenter toward layer 0
  const layer0FinalPos = new Map<string, number>();
  layers[0].forEach((n, i) => layer0FinalPos.set(n, i));

  layers[1].sort((a, b) => {
    const aSources = edges
      .filter((e) => e.to_node === a && layerMap.get(e.from_node) === 0)
      .map((e) => layer0FinalPos.get(e.from_node) ?? 0);
    const bSources = edges
      .filter((e) => e.to_node === b && layerMap.get(e.from_node) === 0)
      .map((e) => layer0FinalPos.get(e.from_node) ?? 0);
    const aAvg = aSources.length
      ? aSources.reduce((x, y) => x + y, 0) / aSources.length
      : 0;
    const bAvg = bSources.length
      ? bSources.reduce((x, y) => x + y, 0) / bSources.length
      : 0;
    return aAvg - bAvg;
  });

  // Step 4: assign final positions
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
    const np = layoutNodes(model.nodes, model.edges, lm);
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
          {/* Arrow markers for causal (blue) edges */}
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

          {/* Glow filter for active edge */}
          <filter id="glow-active" filterUnits="userSpaceOnUse" x="0" y="0" width={SVG_WIDTH} height={SVG_HEIGHT}>
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feColorMatrix
              in="blur"
              type="matrix"
              values="0 0 0 0 0.545  0 0 0 0 0.129  0 0 0 0 0.737  0 0 0 0.7 0"
              result="glow"
            />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {model.edges.map((edge) => {
          const from = nodePositions.get(edge.from_node);
          const to = nodePositions.get(edge.to_node);
          if (!from || !to) return null;

          const isActive = activeEdgeId === edge.id;
          const sameLayer = from.layer === to.layer;

          const selectedMu = edge.selected_option !== null
            ? edge.options[edge.selected_option!].mu
            : edge.options[edge.default_option].mu;

          // --- Visual style: color and thickness always driven by mu ---
          const colorIdx = muToColorIndex(selectedMu);
          const color = isActive ? ACTIVE_COLOR : EDGE_COLORS[colorIdx];
          const strokeWidth = 1.5 + selectedMu * 3.5;
          const markerEnd = isActive ? 'url(#arrow-active)' : `url(#arrow-${colorIdx})`;
          // Same-layer (correlational) edges get a dash pattern to distinguish from causal
          const strokeDasharray = sameLayer ? '6 4' : undefined;

          const opacity = isActive ? 1 : 0.85;

          // --- Path routing ---
          let pathD: string;

          if (sameLayer) {
            // Same-layer: curve rightward to avoid overlapping with cross-layer edges
            const fromX = from.x + NODE_W / 2;
            const fromY = from.y + NODE_H / 4;
            const toX = to.x + NODE_W / 2;
            const toY = to.y - NODE_H / 4;
            const bulge = 60;
            const cx = Math.max(fromX, toX) + bulge;
            const cy = (fromY + toY) / 2;
            pathD = `M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`;
          } else {
            // Cross-layer: right edge of source → left edge of target
            const fromX = from.x + NODE_W / 2;
            const fromY = from.y;
            const toX = to.x - NODE_W / 2;
            const toY = to.y;
            const midX = (fromX + toX) / 2;
            const midY = (fromY + toY) / 2;
            const offsetY = (fromY - toY) * 0.25;
            pathD = `M ${fromX} ${fromY} Q ${midX} ${midY - offsetY} ${toX} ${toY}`;
          }

          return (
            <g
              key={edge.id}
              className="cursor-pointer"
              onClick={() => onEdgeClick?.(edge.id)}
              filter={isActive ? 'url(#glow-active)' : undefined}
            >
              {/* Hit area (invisible wider path for easier clicking) */}
              <path
                d={pathD}
                fill="none"
                stroke="transparent"
                strokeWidth={Math.max(strokeWidth + 8, 12)}
              />
              <path
                d={pathD}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                opacity={opacity}
                markerEnd={markerEnd}
                className="transition-all duration-200"
              />
              {isActive && (
                <path
                  d={pathD}
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
          const lineHeight = 17;
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
                className="text-[16px] font-medium pointer-events-none"
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
