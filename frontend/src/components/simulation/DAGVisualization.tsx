/**
 * DAGVisualization - Interactive causal DAG with smart animations.
 *
 * Features:
 * - Hierarchical top-to-bottom layout
 * - Draggable nodes
 * - Animated edges only for selected node connections
 * - Color-coded by variable type
 */

import { useCallback, useMemo, useEffect, useState, useRef, FormEvent } from 'react';
import { createPortal } from 'react-dom';
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
  NodeChange,
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
  onAddNode?: (variable: Variable) => void;
  onDeleteNode?: (variableName: string) => void;
  onAddEdge?: (edge: Edge) => void;
  onDeleteEdge?: (source: string, target: string) => void;
  onNodesChange?: (nodes: Variable[]) => void;
  onSavePositions?: (positions: Record<string, { x: number; y: number }>) => void;
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
  // Create nodes - use saved positions if available, otherwise use {0,0} for layout
  const nodes: Node[] = dag.nodes.map((variable) => ({
    id: variable.name,
    type: 'dagNode',
    position: {
      x: variable.position_x ?? 0,
      y: variable.position_y ?? 0,
    },
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
      selectable: editable, // Allow selection when editable
      focusable: editable, // Allow keyboard focus when editable
      style: {
        strokeWidth: 2, // Keep constant width
        stroke: isConnectedToSelection ? '#f59e0b' : '#94a3b8', // Amber-500 when selected, gray otherwise
        cursor: editable ? 'pointer' : 'default',
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isConnectedToSelection ? '#f59e0b' : '#94a3b8',
      },
    };
  });

  // Apply layout only if nodes don't have saved positions
  const hasSavedPositions = nodes.some(n => {
    const variable = dag.nodes.find(v => v.name === n.id);
    return variable?.position_x != null && variable?.position_y != null;
  });

  const finalNodes = hasSavedPositions ? nodes : getHierarchicalLayout(nodes, edges);
  return { nodes: finalNodes, edges };
}

export function DAGVisualization({
  dag,
  editable = false,
  onEditNode,
  onAddNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
  onNodesChange,
  onSavePositions,
  height = '100%',
}: DAGVisualizationProps) {
  const { fitView } = useReactFlow();
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const savePositionsTimeout = useRef<NodeJS.Timeout>();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeScope, setNewNodeScope] = useState<'user' | 'world'>('user');
  const [newNodeDescription, setNewNodeDescription] = useState('');

  // Convert DAG with selection state
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => dagToReactFlow(dag, selectedNodes, editable, onEditNode, onDeleteNode),
    [dag, selectedNodes, editable, onEditNode, onDeleteNode]
  );

  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);

  // Handle node position changes with debounce
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChangeInternal(changes);

      // Check if any change is a position change
      const hasPositionChange = changes.some(
        (change) => change.type === 'position' && change.dragging === false
      );

      if (hasPositionChange && onSavePositions) {
        // Clear existing timeout
        if (savePositionsTimeout.current) {
          clearTimeout(savePositionsTimeout.current);
        }

        // Debounce save (wait 1s after last move)
        savePositionsTimeout.current = setTimeout(() => {
          // Get current node positions
          const positions: Record<string, { x: number; y: number }> = {};
          nodes.forEach((node) => {
            positions[node.id] = {
              x: node.position.x,
              y: node.position.y,
            };
          });
          onSavePositions(positions);
        }, 1000);
      }
    },
    [onNodesChangeInternal, onSavePositions, nodes]
  );

  // Sync React Flow state when DAG changes (e.g., after add/remove node)
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = dagToReactFlow(
      dag,
      selectedNodes,
      editable,
      onEditNode,
      onDeleteNode
    );
    setNodes(newNodes);
    setEdges(newEdges);
  }, [dag, editable, onEditNode, onDeleteNode, setNodes, setEdges]);

  // Update edge styles when node selection changes (for highlighting connected edges)
  // Use functional update to preserve React Flow's internal selection state
  useEffect(() => {
    setEdges((currentEdges) =>
      currentEdges.map((edge) => {
        const isConnectedToSelection =
          selectedNodes.includes(edge.source) || selectedNodes.includes(edge.target);
        return {
          ...edge,
          animated: isConnectedToSelection,
          style: {
            ...edge.style,
            stroke: isConnectedToSelection ? '#f59e0b' : '#94a3b8',
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isConnectedToSelection ? '#f59e0b' : '#94a3b8',
          },
        };
      })
    );
  }, [selectedNodes, setEdges]);

  // Fit view on mount and when nodes change significantly
  useEffect(() => {
    setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 10);
  }, [fitView, dag.nodes.length]);

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
              selectable: true,
              focusable: true,
              style: { strokeWidth: 2, stroke: '#94a3b8', cursor: 'pointer' },
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

  // Handle adding new node
  const handleAddNode = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      if (!newNodeName.trim()) return;

      // Create new variable
      const newVariable: Variable = {
        name: newNodeName.trim().toLowerCase().replace(/\s+/g, '_'),
        label: newNodeName.trim(),
        variable_type: 'observable',
        scope: newNodeScope,
        description: newNodeDescription.trim() || '',
        unit: null,
        position_x: 200,
        position_y: 200,
      };

      onAddNode?.(newVariable);

      // Reset form
      setNewNodeName('');
      setNewNodeScope('user');
      setNewNodeDescription('');
      setShowAddDialog(false);
    },
    [newNodeName, newNodeScope, newNodeDescription, onAddNode]
  );

  // Minimap colors by scope (user-level vs world-level)
  const getMinimapNodeColor = (node: Node) => {
    const variable = node.data?.variable as Variable | undefined;
    if (!variable) return '#94a3b8';

    return variable.scope === 'user' ? '#7c3aed' : '#06b6d4';
  };

  return (
    <div className="relative w-full bg-slate-50" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={editable ? onEdgesChangeInternal : undefined}
        onSelectionChange={onSelectionChange}
        onConnect={onConnect}
        onEdgesDelete={onEdgesDelete}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
        deleteKeyCode={editable ? ['Delete', 'Backspace'] : null}
        selectionKeyCode={editable ? 'Shift' : null}
        multiSelectionKeyCode={editable ? 'Meta' : null}
        selectNodesOnDrag={false}
        edgesFocusable={editable}
        elementsSelectable={editable}
        defaultEdgeOptions={{
          type: 'default',
          selectable: editable,
          focusable: editable,
          interactionWidth: 20, // Make edges easier to click
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

      {/* Legend - top right, compact */}
      <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-lg border border-slate-200/80 px-3 py-2 text-xs shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#7c3aed' }} />
            <span className="text-slate-600">User-level</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#06b6d4' }} />
            <span className="text-slate-600">World-level</span>
          </div>
        </div>
      </div>

      {/* Add Node Button */}
      {editable && onAddNode && (
        <button
          onClick={() => setShowAddDialog(true)}
          className="absolute bottom-6 right-6 w-12 h-12 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105"
          title="Adicionar variável"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      )}

      {/* Add Node Dialog */}
      {showAddDialog &&
        createPortal(
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[99999]">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Nova Variável
              </h3>

              <form onSubmit={handleAddNode} className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Nome
                  </label>
                  <input
                    type="text"
                    value={newNodeName}
                    onChange={(e) => setNewNodeName(e.target.value)}
                    placeholder="Ex: taxa_conversao"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    autoFocus
                    required
                  />
                </div>

                {/* Scope */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Escopo
                  </label>
                  <div className="flex gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="scope"
                        value="user"
                        checked={newNodeScope === 'user'}
                        onChange={() => setNewNodeScope('user')}
                        className="text-indigo-600 focus:ring-indigo-500"
                      />
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#7c3aed' }} />
                        <span className="text-sm text-slate-700">User-level</span>
                      </div>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="scope"
                        value="world"
                        checked={newNodeScope === 'world'}
                        onChange={() => setNewNodeScope('world')}
                        className="text-indigo-600 focus:ring-indigo-500"
                      />
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#06b6d4' }} />
                        <span className="text-sm text-slate-700">World-level</span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Descrição (opcional)
                  </label>
                  <textarea
                    value={newNodeDescription}
                    onChange={(e) => setNewNodeDescription(e.target.value)}
                    placeholder="Descreva o que esta variável representa..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddDialog(false);
                      setNewNodeName('');
                      setNewNodeDescription('');
                    }}
                    className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                  >
                    Adicionar
                  </button>
                </div>
              </form>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
