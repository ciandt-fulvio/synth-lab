/**
 * CausalDAGView component.
 *
 * Cytoscape.js-based visualization of the causal DAG with 3-layer layout:
 * - Left: demographic root nodes
 * - Center: mediator nodes
 * - Right: outcome node
 *
 * Edges:
 *   - Cross-layer (causal): solid bezier curves with arrows, width varies by mu
 *   - Same-layer (correlational, between mediators): dashed, fixed width
 *
 * Node ordering uses a barycenter heuristic to minimize edge crossings.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Spec: specs/042-quantitative-analysis/spec.md
 *   - Cytoscape.js: https://js.cytoscape.org
 *   - react-cytoscapejs: https://github.com/plotly/react-cytoscapejs
 */

import { useMemo, useRef, useEffect } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import type cytoscape from 'cytoscape';
import type { CausalModel, CausalEdge } from '@/types/quantitative-analysis';

interface CausalDAGViewProps {
  model: CausalModel;
  activeEdgeId?: string | null;
  onEdgeClick?: (edgeId: string) => void;
}

// --- Layout constants ---
const CANVAS_H = 500;
const LAYER_X = [140, 480, 820];

// --- Color palette ---
const EDGE_COLORS = ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1e40af'];
const ACTIVE_EDGE_COLOR = '#7c3aed';

const LAYER_STYLES = [
  { bg: '#f1f5f9', border: '#cbd5e1', text: '#334155' }, // slate (demographics)
  { bg: '#f5f3ff', border: '#c4b5fd', text: '#5b21b6' }, // violet (mediators)
  { bg: '#ecfdf5', border: '#6ee7b7', text: '#047857' }, // emerald (outcome)
];

function muToColorIndex(mu: number): number {
  return Math.min(Math.floor(mu * EDGE_COLORS.length), EDGE_COLORS.length - 1);
}

/**
 * Classify nodes into 3 layers based on edge topology.
 * Layer 0: only appear as "from" (roots/demographics)
 * Layer 2: only appear as "to" (outcome)
 * Layer 1: everything else (mediators)
 */
function classifyNodes(nodes: string[], edges: CausalEdge[]): Map<string, number> {
  const fromNodes = new Set(edges.map((e) => e.from_node));
  const toNodes = new Set(edges.map((e) => e.to_node));
  const layerMap = new Map<string, number>();

  for (const node of nodes) {
    const isFrom = fromNodes.has(node);
    const isTo = toNodes.has(node);
    if (isFrom && !isTo) layerMap.set(node, 0);
    else if (isTo && !isFrom) layerMap.set(node, 2);
    else layerMap.set(node, 1);
  }

  return layerMap;
}

/**
 * Layout nodes using barycenter heuristic for edge crossing minimization.
 */
function computePositions(
  nodes: string[],
  edges: CausalEdge[],
  layerMap: Map<string, number>
): Map<string, { x: number; y: number }> {
  const layers: string[][] = [[], [], []];
  for (const node of nodes) {
    layers[layerMap.get(node) ?? 1].push(node);
  }

  // Barycenter: sort layer 1 initial indices
  const l1Init = new Map<string, number>();
  layers[1].forEach((n, i) => l1Init.set(n, i));

  // Sort layer 0 by avg position of layer-1 targets
  layers[0].sort((a, b) => {
    const avg = (nd: string) => {
      const targets = edges
        .filter((e) => e.from_node === nd && layerMap.get(e.to_node) === 1)
        .map((e) => l1Init.get(e.to_node) ?? 0);
      return targets.length ? targets.reduce((x, y) => x + y, 0) / targets.length : 0;
    };
    return avg(a) - avg(b);
  });

  // Re-index layer 0, then sort layer 1 by avg position of layer-0 sources
  const l0Final = new Map<string, number>();
  layers[0].forEach((n, i) => l0Final.set(n, i));

  layers[1].sort((a, b) => {
    const avg = (nd: string) => {
      const sources = edges
        .filter((e) => e.to_node === nd && layerMap.get(e.from_node) === 0)
        .map((e) => l0Final.get(e.from_node) ?? 0);
      return sources.length ? sources.reduce((x, y) => x + y, 0) / sources.length : 0;
    };
    return avg(a) - avg(b);
  });

  // Assign positions
  const positions = new Map<string, { x: number; y: number }>();
  for (let layer = 0; layer < 3; layer++) {
    const count = layers[layer].length;
    const spacing = CANVAS_H / (count + 1);
    layers[layer].forEach((node, idx) => {
      positions.set(node, { x: LAYER_X[layer], y: spacing * (idx + 1) });
    });
  }

  return positions;
}

/** Build cytoscape elements from model data. */
function buildElements(
  model: CausalModel,
  layerMap: Map<string, number>,
  positions: Map<string, { x: number; y: number }>
): cytoscape.ElementDefinition[] {
  const elements: cytoscape.ElementDefinition[] = [];

  for (const node of model.nodes) {
    const layer = layerMap.get(node) ?? 1;
    const pos = positions.get(node);
    if (!pos) continue;
    elements.push({
      data: { id: node, label: node, layer },
      position: { x: pos.x, y: pos.y },
    });
  }

  for (const edge of model.edges) {
    const fromLayer = layerMap.get(edge.from_node) ?? 1;
    const toLayer = layerMap.get(edge.to_node) ?? 1;
    const sameLayer = fromLayer === toLayer;
    const selectedMu =
      edge.selected_option !== null
        ? edge.options[edge.selected_option].mu
        : edge.options[edge.default_option].mu;
    const colorIdx = muToColorIndex(selectedMu);
    const width = 1.5 + selectedMu * 3.5;

    elements.push({
      data: {
        id: edge.id,
        source: edge.from_node,
        target: edge.to_node,
        edgeColor: EDGE_COLORS[colorIdx],
        edgeWidth: width,
        sameLayer,
        mu: selectedMu,
      },
    });
  }

  return elements;
}

/** Cytoscape stylesheet (static, no active edge baked in). */
const BASE_STYLESHEET: cytoscape.Stylesheet[] = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      shape: 'round-rectangle',
      width: 120,
      height: 60,
      'background-color': '#f1f5f9',
      'border-width': 1.5,
      'border-color': '#cbd5e1',
      color: '#334155',
      'font-size': '11px',
      'font-weight': 500,
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '100px',
      'text-overflow-wrap': 'anywhere',
    },
  },
  {
    selector: 'node[layer = 0]',
    style: {
      'background-color': LAYER_STYLES[0].bg,
      'border-color': LAYER_STYLES[0].border,
      color: LAYER_STYLES[0].text,
    },
  },
  {
    selector: 'node[layer = 1]',
    style: {
      'background-color': LAYER_STYLES[1].bg,
      'border-color': LAYER_STYLES[1].border,
      color: LAYER_STYLES[1].text,
    },
  },
  {
    selector: 'node[layer = 2]',
    style: {
      'background-color': LAYER_STYLES[2].bg,
      'border-color': LAYER_STYLES[2].border,
      color: LAYER_STYLES[2].text,
    },
  },
  // Cross-layer (causal) edges
  {
    selector: 'edge[!sameLayer]',
    style: {
      width: 'data(edgeWidth)' as any,
      'line-color': 'data(edgeColor)',
      'target-arrow-color': 'data(edgeColor)',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 0.8,
      'curve-style': 'bezier',
      opacity: 0.85,
    },
  },
  // Same-layer (correlational) edges — dashed
  {
    selector: 'edge[?sameLayer]',
    style: {
      width: 'data(edgeWidth)' as any,
      'line-color': 'data(edgeColor)',
      'target-arrow-color': 'data(edgeColor)',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 0.8,
      'curve-style': 'unbundled-bezier',
      'control-point-distances': [80] as any,
      'control-point-weights': [0.5] as any,
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4] as any,
      opacity: 0.85,
    },
  },
];

export function CausalDAGView({ model, activeEdgeId, onEdgeClick }: CausalDAGViewProps) {
  const cyRef = useRef<cytoscape.Core | null>(null);
  const onEdgeClickRef = useRef(onEdgeClick);
  onEdgeClickRef.current = onEdgeClick;

  const { layerMap, positions } = useMemo(() => {
    const lm = classifyNodes(model.nodes, model.edges);
    const pos = computePositions(model.nodes, model.edges, lm);
    return { layerMap: lm, positions: pos };
  }, [model.nodes, model.edges]);

  const elements = useMemo(
    () => buildElements(model, layerMap, positions),
    [model, layerMap, positions]
  );

  // Handle cy instance ref — runs once per mount
  const handleCyRef = (cy: cytoscape.Core) => {
    if (cyRef.current === cy) return;
    cyRef.current = cy;

    // Disable node dragging
    cy.nodes().ungrabify();

    // Edge click handler
    cy.on('tap', 'edge', (evt) => {
      onEdgeClickRef.current?.(evt.target.id());
    });

    // Fit with padding — use multiple attempts to handle container resize
    const fitGraph = () => {
      cy.resize();
      cy.fit(undefined, 50);
    };
    // Immediate + delayed fits to handle layout timing
    fitGraph();
    setTimeout(fitGraph, 50);
    setTimeout(fitGraph, 200);
  };

  // Apply active edge highlight imperatively to avoid full re-render
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.edges().forEach((edge) => {
      const isActive = edge.id() === activeEdgeId;
      if (isActive) {
        edge.style({
          'line-color': ACTIVE_EDGE_COLOR,
          'target-arrow-color': ACTIVE_EDGE_COLOR,
          width: Math.max(edge.data('edgeWidth') + 2, 5),
          opacity: 1,
          'z-index': 10,
          'overlay-color': ACTIVE_EDGE_COLOR,
          'overlay-padding': 5,
          'overlay-opacity': 0.12,
        } as any);
      } else {
        edge.style({
          'line-color': edge.data('edgeColor'),
          'target-arrow-color': edge.data('edgeColor'),
          width: edge.data('edgeWidth'),
          opacity: activeEdgeId ? 0.4 : 0.85,
          'z-index': 0,
          'overlay-opacity': 0,
          'overlay-padding': 0,
        } as any);
      }
    });
  }, [activeEdgeId]);

  // Re-fit when elements change (new model generated)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().ungrabify();
    const t = setTimeout(() => {
      cy.fit(undefined, 40);
      cy.center();
    }, 100);
    return () => clearTimeout(t);
  }, [elements]);

  return (
    <div className="w-full" style={{ height: 440 }}>
      <CytoscapeComponent
        elements={elements}
        stylesheet={BASE_STYLESHEET}
        layout={{ name: 'preset' }}
        style={{ width: '100%', height: '100%' }}
        cy={handleCyRef}
        userPanningEnabled={true}
        userZoomingEnabled={true}
        boxSelectionEnabled={false}
        autoungrabify={true}
        minZoom={0.3}
        maxZoom={2.5}
      />
    </div>
  );
}
