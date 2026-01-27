/**
 * DAGVisualization - Interactive causal DAG with smart animations.
 *
 * Features:
 * - Hierarchical top-to-bottom layout
 * - Draggable nodes
 * - Animated edges only for selected node connections
 * - Color-coded by variable type
 */

import { useCallback, useMemo, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge as RFEdge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  BackgroundVariant,
  useReactFlow,
  OnSelectionChangeParams,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DAGNodeCard } from './DAGNodeCard';
import type { CausalDAG, Variable, Edge } from '@/types/causal-dag';

const nodeTypes = {
  dagNode: DAGNodeCard,
};

// Layout constants - LEFT-TO-RIGHT orientation
const NODE_WIDTH = 220;
const NODE_HEIGHT = 80;
const LEVEL_SPACING = 350; // Spacing between levels (horizontal)
const NODE_SPACING = 120; // Spacing between nodes in same level (vertical)

interface DAGVisualizationProps {
  dag: CausalDAG;
  editable?: boolean;
  onEditNode?: (variable: Variable) => void;
  onDeleteNode?: (variableName: string) => void;
  onAddEdge?: (edge: Edge) => void;
  onDeleteEdge?: (source: string, target: string) => void;
  onNodesChange?: (nodes: Variable[]) => void;
  height?: string | number;
}

/**
 * Simple hierarchical layout using topological sorting.
 */
function getHierarchicalLayout(nodes: Node[], edges: RFEdge[]): Node[] {
  const adjacency = new Map<string, Set<string>>();
  const inDegree = new Map<string, number>();

  nodes.forEach(node => {
    adjacency.set(node.id, new Set());
    inDegree.set(node.id, 0);
  });

  edges.forEach(edge => {
    adjacency.get(edge.source)?.add(edge.target);
    inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
  });

  const levels: string[][] = [];
  const nodeLevel = new Map<string, number>();
  const queue: string[] = [];

  // Start with root nodes
  nodes.forEach(node => {
    if (inDegree.get(node.id) === 0) {
      queue.push(node.id);
      nodeLevel.set(node.id, 0);
    }
  });

  // BFS to assign levels
  while (queue.length > 0) {
    const current = queue.shift()!;
    const level = nodeLevel.get(current)!;

    if (!levels[level]) {
      levels[level] = [];
    }
    levels[level].push(current);

    adjacency.get(current)?.forEach(neighbor => {
      const newDegree = (inDegree.get(neighbor) || 0) - 1;
      inDegree.set(neighbor, newDegree);

      if (newDegree === 0) {
        queue.push(neighbor);
        nodeLevel.set(neighbor, level + 1);
      }
    });
  }

  // Handle orphan nodes
  nodes.forEach(node => {
    if (!nodeLevel.has(node.id)) {
      const level = levels.length;
      if (!levels[level]) {
        levels[level] = [];
      }
      levels[level].push(node.id);
      nodeLevel.set(node.id, level);
    }
  });

  // Position nodes LEFT-TO-RIGHT (levels go horizontally, nodes in level stack vertically)
  return nodes.map(node => {
    const level = nodeLevel.get(node.id) || 0;
    const nodesInLevel = levels[level] || [];
    const indexInLevel = nodesInLevel.indexOf(node.id);

    // Center nodes vertically
    const totalHeight = nodesInLevel.length * NODE_SPACING;
    const startY = -totalHeight / 2;

    return {
      ...node,
      position: {
        x: level * LEVEL_SPACING + 100, // Horizontal progression (levels)
        y: startY + indexInLevel * NODE_SPACING + NODE_SPACING / 2, // Vertical stacking (nodes in same level)
      },
    };
  });
}

/**
 * Get edges connected to a node.
 */
function getConnectedEdges(nodeId: string, edges: RFEdge[]): Set<string> {
  const connected = new Set<string>();
  edges.forEach(edge => {
    if (edge.source === nodeId || edge.target === nodeId) {
      connected.add(edge.id);
    }
  });
  return connected;
}

/**
 * Convert DAG to React Flow format.
 */
function dagToReactFlow(
  dag: CausalDAG,
  selectedNodes: string[],
  editable: boolean,
  onEditNode?: (variable: Variable) => void,
  onDeleteNode?: (variableName: string) => void
): { nodes: Node[]; edges: RFEdge[] } {
  // Create nodes - always draggable for better UX
  const nodes: Node[] = dag.nodes.map((variable) => ({
    id: variable.name,
    type: 'dagNode',
    position: { x: 0, y: 0 },
    data: {
      variable,
      onEdit: editable ? onEditNode : undefined,
      onDelete: editable ? onDeleteNode : undefined,
    },
    draggable: true, // Always allow dragging
  }));

  // Get connected edges if a node is selected
  const selectedEdgeIds = new Set<string>();
  if (selectedNodes.length > 0) {
    selectedNodes.forEach(nodeId => {
      const tempEdges = dag.edges.map(e => ({
        id: `${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
      }));
      const connected = getConnectedEdges(nodeId, tempEdges);
      connected.forEach(id => selectedEdgeIds.add(id));
    });
  }

  // Create edges - gray by default, highlight when connected to selected node
  const edges: RFEdge[] = dag.edges.map((edge) => {
    const edgeId = `${edge.source}-${edge.target}`;
    const isConnectedToSelection = selectedEdgeIds.has(edgeId);

    return {
      id: edgeId,
      source: edge.source,
      target: edge.target,
      type: 'default',
      animated: isConnectedToSelection, // Animate only selected edges
      style: {
        strokeWidth: 2, // Keep constant width
        stroke: isConnectedToSelection ? '#f59e0b' : '#94a3b8', // Amber-500 when selected, gray otherwise
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isConnectedToSelection ? '#f59e0b' : '#94a3b8',
      },
    };
  });

  // Apply layout
  const layoutedNodes = getHierarchicalLayout(nodes, edges);
  return { nodes: layoutedNodes, edges };
}

export function DAGVisualization({
  dag,
  editable = false,
  onEditNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
  onNodesChange,
  height = '100%',
}: DAGVisualizationProps) {
  const { fitView } = useReactFlow();
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);

  // Convert DAG with selection state
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => dagToReactFlow(dag, selectedNodes, editable, onEditNode, onDeleteNode),
    [dag, selectedNodes, editable, onEditNode, onDeleteNode]
  );

  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);

  // Update edges when selection changes
  useEffect(() => {
    const { edges: updatedEdges } = dagToReactFlow(dag, selectedNodes, editable, onEditNode, onDeleteNode);
    setEdges(updatedEdges);
  }, [selectedNodes, dag, editable, onEditNode, onDeleteNode, setEdges]);

  // Fit view on mount
  useEffect(() => {
    setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 10);
  }, [fitView, initialNodes]);

  // Track selection changes
  const onSelectionChange = useCallback(({ nodes }: OnSelectionChangeParams) => {
    setSelectedNodes(nodes.map(n => n.id));
  }, []);

  // Handle new edge connection
  const onConnect = useCallback(
    (params: Connection) => {
      if (!editable) return;

      if (params.source && params.target) {
        const newEdge: Edge = {
          source: params.source,
          target: params.target,
          relationship_type: 'causal',
          strength: null,
          description: null,
        };
        onAddEdge?.(newEdge);

        setEdges((eds) =>
          addEdge(
            {
              ...params,
              type: 'default',
              animated: false,
              style: { strokeWidth: 2, stroke: '#94a3b8' },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
            },
            eds
          )
        );
      }
    },
    [editable, onAddEdge, setEdges]
  );

  // Handle edge deletion
  const onEdgesDelete = useCallback(
    (deletedEdges: RFEdge[]) => {
      if (!editable) return;
      deletedEdges.forEach((edge) => {
        onDeleteEdge?.(edge.source, edge.target);
      });
    },
    [editable, onDeleteEdge]
  );

  // Minimap colors by scope (user-level vs world-level)
  const getMinimapNodeColor = (node: Node) => {
    const variable = node.data?.variable as Variable | undefined;
    if (!variable) return '#94a3b8';

    return variable.scope === 'user' ? '#4f46e5' : '#818cf8';
  };

  return (
    <div className="relative w-full bg-slate-50" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChangeInternal}
        onEdgesChange={editable ? onEdgesChangeInternal : undefined}
        onSelectionChange={onSelectionChange}
        onConnect={onConnect}
        onEdgesDelete={onEdgesDelete}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'default',
        }}
        connectionLineStyle={{ strokeWidth: 2, stroke: '#94a3b8' }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#cbd5e1" />

        <MiniMap
          nodeColor={getMinimapNodeColor}
          maskColor="rgba(0, 0, 0, 0.05)"
          className="!bg-white/80 !border !border-slate-200 !rounded-lg"
          style={{ width: 140, height: 100 }}
        />

        <Controls
          showInteractive={false}
          className="!bg-white/80 !border !border-slate-200 !rounded-lg"
        />
      </ReactFlow>

      {/* Simplified Legend - scope only */}
      <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-slate-200 p-3 text-xs shadow-lg">
        <div className="font-semibold text-slate-700 mb-2">Variáveis</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#4f46e5' }} />
            <span className="text-slate-600">User-level</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#818cf8' }} />
            <span className="text-slate-600">World-level</span>
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-200 text-[10px] text-slate-500">
          Clique em um nó para destacar conexões
        </div>
      </div>
    </div>
  );
}
