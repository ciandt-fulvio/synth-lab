/**
 * CausalDAGView component.
 *
 * Cytoscape.js ELK (left→right) visualization of the enriched causal DAG.
 *
 * Node filtering:
 *   - Demographic nodes are always hidden (implicit — they feed sensitivities).
 *   - All edges from/to demographic nodes are hidden.
 *
 * Layers (ELK infers from graph):
 *   - sensitivity (left)
 *   - product
 *   - interaction
 *   - outcome (right)
 *
 * Colors:
 *   - sensitivity: blue light
 *   - product: lilac
 *   - interaction: yellow
 *   - outcome: green
 *
 * Tooltip: hovering a node shows a floating tooltip with LLM-generated description.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Cytoscape.js: https://js.cytoscape.org
 *   - cytoscape-elk: https://github.com/cytoscape/cytoscape.js-elk
 */

import { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
// @ts-expect-error — no type declarations for cytoscape-elk
import elk from 'cytoscape-elk';
import type { CausalModel, NodeType } from '@/types/quantitative-analysis';

// Register ELK layout once
cytoscape.use(elk);

interface CausalDAGViewProps {
  model: CausalModel;
  activeEdgeId?: string | null;
  onEdgeClick?: (edgeId: string) => void;
  onNodeClick?: (nodeName: string) => void;
}

interface TooltipData {
  label: string;
  nodeType: NodeType;
  description: string;
  x: number;
  y: number;
}

// --- Color palette by node type ---
const NODE_STYLES: Record<NodeType, { bg: string; border: string; text: string }> = {
  demographic: { bg: '#dbeafe', border: '#93c5fd', text: '#1e40af' },
  sensitivity: { bg: '#dbeafe', border: '#93c5fd', text: '#1e40af' },
  product: { bg: '#ede9fe', border: '#c4b5fd', text: '#6d28d9' },
  interaction: { bg: '#fef9c3', border: '#fde047', text: '#854d0e' },
  outcome: { bg: '#dcfce7', border: '#86efac', text: '#166534' },
};

const NODE_TYPE_LABELS: Record<NodeType, string> = {
  demographic: 'Usuário',
  sensitivity: 'Usuário',
  product: 'Produto',
  interaction: 'Interação',
  outcome: 'Resultado',
};

// Node type rank (used as data attribute, ELK infers layers from graph structure)
const NODE_TYPE_RANK: Record<NodeType, number> = {
  demographic: 0,
  sensitivity: 1,
  product: 2,
  interaction: 3,
  outcome: 4,
};

const EDGE_COLORS = ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1e40af'];
const ACTIVE_EDGE_COLOR = '#7c3aed';
const FIXED_EDGE_COLOR = '#94a3b8';

function muToColorIndex(mu: number): number {
  return Math.min(Math.floor(mu * EDGE_COLORS.length), EDGE_COLORS.length - 1);
}

/**
 * Get node type from node_metadata, with topology-based fallback.
 */
function getNodeType(
  nodeName: string,
  model: CausalModel,
  fromNodes: Set<string>,
  toNodes: Set<string>
): NodeType {
  const meta = model.node_metadata?.[nodeName];
  if (meta?.node_type) return meta.node_type;

  const isFrom = fromNodes.has(nodeName);
  const isTo = toNodes.has(nodeName);
  if (isFrom && !isTo) return 'demographic';
  if (isTo && !isFrom) return 'outcome';
  return 'sensitivity';
}

/**
 * Build a tooltip description for a node, preferring LLM-generated description.
 */
function buildNodeDescription(nodeName: string, nodeType: NodeType, model: CausalModel): string {
  const meta = model.node_metadata?.[nodeName];

  // Use LLM-generated description if available
  if (meta?.description) return meta.description;

  // Fallback descriptions
  const fromNodes = new Set(model.edges.map((e) => e.from_node));
  const toNodes = new Set(model.edges.map((e) => e.to_node));

  switch (nodeType) {
    case 'demographic':
      return 'Variável demográfica extraída dos dados do synth.';
    case 'sensitivity': {
      const key = meta?.sensitivity_key;
      if (key?.startsWith('custom_')) return 'Sensitividade personalizada criada pela IA.';
      if (key) return `Sensitividade derivada das regras do sistema (${key}).`;
      return 'Sensitividade comportamental do usuário.';
    }
    case 'product': {
      const desc = meta?.product_description;
      const cal = meta?.product_calibration ?? 'medium';
      const calLabel = cal === 'low' ? 'Baixo' : cal === 'high' ? 'Alto' : 'Médio';
      return desc
        ? `${desc} — Calibração: ${calLabel}`
        : `Característica do produto — Calibração: ${calLabel}`;
    }
    case 'interaction': {
      const parents = model.edges
        .filter((e) => e.to_node === nodeName)
        .map((e) => e.from_node)
        .filter((p) => getNodeType(p, model, fromNodes, toNodes) !== 'demographic');
      if (parents.length >= 2) {
        return `Interação entre ${parents.join(' e ')}.`;
      }
      if (parents.length === 1) {
        return `Derivado de ${parents[0]}.`;
      }
      return 'Nó de interação endógeno.';
    }
    case 'outcome':
      return 'Variável de resultado final calculada pela simulação Monte Carlo.';
  }
}

/**
 * Get visible nodes: hide all demographic nodes.
 */
function getVisibleNodes(model: CausalModel): Set<string> {
  const fromNodes = new Set(model.edges.map((e) => e.from_node));
  const toNodes = new Set(model.edges.map((e) => e.to_node));
  const visible = new Set<string>();

  for (const node of model.nodes) {
    const nodeType = getNodeType(node, model, fromNodes, toNodes);
    if (nodeType !== 'demographic') {
      visible.add(node);
    }
  }

  return visible;
}

/** Build cytoscape elements from model data. */
function buildElements(model: CausalModel): cytoscape.ElementDefinition[] {
  const elements: cytoscape.ElementDefinition[] = [];
  const fromNodes = new Set(model.edges.map((e) => e.from_node));
  const toNodes = new Set(model.edges.map((e) => e.to_node));
  const visibleNodes = getVisibleNodes(model);

  for (const node of model.nodes) {
    if (!visibleNodes.has(node)) continue;

    const nodeType = getNodeType(node, model, fromNodes, toNodes);
    const style = NODE_STYLES[nodeType];
    const rank = NODE_TYPE_RANK[nodeType];

    elements.push({
      data: {
        id: node,
        label: node,
        nodeType,
        rank,
        bgColor: style.bg,
        borderColor: style.border,
        textColor: style.text,
      },
    });
  }

  for (const edge of model.edges) {
    // Skip edges involving hidden nodes
    if (!visibleNodes.has(edge.from_node) || !visibleNodes.has(edge.to_node)) continue;

    const isFixed = edge.edge_type === 'fixed';

    let edgeColor = FIXED_EDGE_COLOR;
    let width = 1.5;

    if (!isFixed && edge.options.length > 0) {
      const selectedMu =
        edge.selected_option !== null
          ? edge.options[edge.selected_option]?.mu ?? 0.5
          : edge.options[edge.default_option]?.mu ?? 0.5;
      const colorIdx = muToColorIndex(selectedMu);
      edgeColor = EDGE_COLORS[colorIdx];
      width = 1.5 + selectedMu * 3.5;
    }

    elements.push({
      data: {
        id: edge.id,
        source: edge.from_node,
        target: edge.to_node,
        edgeColor,
        edgeWidth: width,
        isFixed,
      },
    });
  }

  return elements;
}

/** Cytoscape stylesheet. */
const BASE_STYLESHEET: cytoscape.Stylesheet[] = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      shape: 'round-rectangle',
      width: 140,
      height: 44,
      'background-color': 'data(bgColor)' as any,
      'border-width': 1.5,
      'border-color': 'data(borderColor)' as any,
      color: 'data(textColor)' as any,
      'font-size': '11px',
      'font-weight': 500,
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '120px',
      'text-overflow-wrap': 'whitespace',
      'cursor': 'pointer',
    },
  },
  // Likert edges — solid
  {
    selector: 'edge[!isFixed]',
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
  // Fixed edges — dashed, thinner, gray
  {
    selector: 'edge[?isFixed]',
    style: {
      width: 1.5,
      'line-color': FIXED_EDGE_COLOR,
      'target-arrow-color': FIXED_EDGE_COLOR,
      'target-arrow-shape': 'triangle',
      'arrow-scale': 0.6,
      'curve-style': 'bezier',
      'line-style': 'dashed',
      'line-dash-pattern': [5, 3] as any,
      opacity: 0.55,
    },
  },
];

/** ELK layered layout — left to right, with crossing minimization. */
const ELK_LAYOUT = {
  name: 'elk',
  elk: {
    algorithm: 'layered',
    'elk.direction': 'RIGHT',
    'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
    'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
    'elk.layered.spacing.nodeNodeBetweenLayers': '80',
    'elk.spacing.nodeNode': '32',
    'elk.spacing.edgeNode': '20',
    'elk.spacing.edgeEdge': '15',
    'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
  },
  animate: false,
  fit: true,
  padding: 30,
};

/** Tooltip overlay component. */
function NodeTooltip({ data }: { data: TooltipData }) {
  const style = NODE_STYLES[data.nodeType];

  return (
    <div
      className="absolute z-50 bg-white rounded-lg shadow-lg border border-slate-200 p-3 max-w-[280px] pointer-events-none"
      style={{ left: data.x, top: data.y, transform: 'translate(-50%, 8px)' }}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span
          className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
          style={{ backgroundColor: style.border }}
        />
        <span className="font-semibold text-sm text-slate-800 truncate">{data.label}</span>
      </div>
      <span
        className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded mb-1.5"
        style={{ backgroundColor: style.bg, color: style.text }}
      >
        {NODE_TYPE_LABELS[data.nodeType]}
      </span>
      <p className="text-xs text-slate-600 leading-relaxed">{data.description}</p>
    </div>
  );
}

export function CausalDAGView({ model, activeEdgeId, onEdgeClick, onNodeClick }: CausalDAGViewProps) {
  const cyRef = useRef<cytoscape.Core | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const onEdgeClickRef = useRef(onEdgeClick);
  onEdgeClickRef.current = onEdgeClick;
  const onNodeClickRef = useRef(onNodeClick);
  onNodeClickRef.current = onNodeClick;
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  const elements = useMemo(() => buildElements(model), [model]);

  const showTooltipForNode = useCallback(
    (node: cytoscape.NodeSingular) => {
      const cy = cyRef.current;
      const container = containerRef.current;
      if (!cy || !container) return;

      const nodeName = node.id();
      const fromNodes = new Set(model.edges.map((e) => e.from_node));
      const toNodes = new Set(model.edges.map((e) => e.to_node));
      const resolvedType = getNodeType(nodeName, model, fromNodes, toNodes);
      const description = buildNodeDescription(nodeName, resolvedType, model);

      const pos = node.renderedPosition();
      const rect = container.getBoundingClientRect();
      const cyRect = cy.container()?.getBoundingClientRect();
      const offsetX = cyRect ? cyRect.left - rect.left : 0;
      const offsetY = cyRect ? cyRect.top - rect.top : 0;

      setTooltip({
        label: nodeName,
        nodeType: resolvedType,
        description,
        x: pos.x + offsetX,
        y: pos.y + offsetY + node.renderedHeight() / 2,
      });
    },
    [model]
  );

  // Handle cy instance ref
  const handleCyRef = useCallback(
    (cy: cytoscape.Core) => {
      if (cyRef.current === cy) return;
      cyRef.current = cy;

      cy.nodes().ungrabify();

      // Tooltip on hover
      cy.on('mouseover', 'node', (evt) => showTooltipForNode(evt.target));
      cy.on('mouseout', 'node', () => setTooltip(null));

      // Edge click
      cy.on('tap', 'edge', (evt) => {
        onEdgeClickRef.current?.(evt.target.id());
      });

      // Node click — only for interaction/outcome nodes
      cy.on('tap', 'node', (evt) => {
        const nodeType = evt.target.data('nodeType');
        if (nodeType === 'interaction' || nodeType === 'outcome') {
          onNodeClickRef.current?.(evt.target.id());
        }
      });
    },
    [showTooltipForNode]
  );

  // Re-run layout when elements change (e.g. after model regeneration)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || cy.elements().length === 0) return;

    // Small delay to let react-cytoscapejs sync elements first
    const timer = setTimeout(() => {
      cy.layout(ELK_LAYOUT as any).run();
      cy.fit(undefined, 30);
      cy.nodes().ungrabify();
    }, 50);

    return () => clearTimeout(timer);
  }, [elements]);

  // Apply active edge highlight imperatively
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
        const isFixed = edge.data('isFixed');
        edge.style({
          'line-color': isFixed ? FIXED_EDGE_COLOR : edge.data('edgeColor'),
          'target-arrow-color': isFixed ? FIXED_EDGE_COLOR : edge.data('edgeColor'),
          width: isFixed ? 1.5 : edge.data('edgeWidth'),
          opacity: activeEdgeId ? (isFixed ? 0.3 : 0.4) : (isFixed ? 0.55 : 0.85),
          'z-index': 0,
          'overlay-opacity': 0,
          'overlay-padding': 0,
        } as any);
      }
    });
  }, [activeEdgeId]);

  // Dismiss tooltip on zoom/pan
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const dismiss = () => setTooltip(null);
    cy.on('zoom pan', dismiss);
    return () => {
      cy.off('zoom pan', dismiss);
    };
  }, [elements]);

  return (
    <div ref={containerRef} className="w-full h-full relative" style={{ minHeight: 380 }}>
      <CytoscapeComponent
        elements={elements}
        stylesheet={BASE_STYLESHEET}
        layout={ELK_LAYOUT as any}
        style={{ width: '100%', height: '100%' }}
        cy={handleCyRef}
        userPanningEnabled={true}
        userZoomingEnabled={true}
        boxSelectionEnabled={false}
        autoungrabify={true}
        minZoom={0.3}
        maxZoom={2.5}
      />
      {tooltip && <NodeTooltip data={tooltip} />}
    </div>
  );
}
