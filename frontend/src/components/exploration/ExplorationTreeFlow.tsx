/**
 * ExplorationTreeFlow component.
 *
 * React Flow based tree visualization with horizontal layout.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md
 *   - Library: https://reactflow.dev/
 */

import { useCallback, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  type NodeTypes,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { DecisionNode } from './DecisionNode';
import { buildReactFlowElements } from '@/lib/exploration-utils';
import type { ScenarioNode, DecisionNodeData } from '@/types/exploration';
import { cn } from '@/lib/utils';

const nodeTypes: NodeTypes = {
  decision: DecisionNode,
};

interface ExplorationTreeFlowProps {
  /** Array of scenario nodes from API */
  nodes: ScenarioNode[];
  /** Callback when a node is clicked */
  onNodeClick?: (node: ScenarioNode) => void;
  /** Currently selected node ID */
  selectedNodeId?: string | null;
  /** Winner node ID for path highlighting */
  winnerNodeId?: string | null;
  /** Optional className for container */
  className?: string;
}

export function ExplorationTreeFlow({
  nodes,
  onNodeClick,
  selectedNodeId,
  winnerNodeId,
  className = '',
}: ExplorationTreeFlowProps) {
  // Build React Flow elements with memoization
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => buildReactFlowElements(nodes, winnerNodeId),
    [nodes, winnerNodeId]
  );

  const [rfNodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [rfEdges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync when source data changes
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = buildReactFlowElements(
      nodes,
      winnerNodeId
    );
    setNodes(newNodes);
    setEdges(newEdges);
  }, [nodes, winnerNodeId, setNodes, setEdges]);

  // Update selected state when selectedNodeId changes
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === selectedNodeId,
      }))
    );
  }, [selectedNodeId, setNodes]);

  // Handle node click
  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<DecisionNodeData>) => {
      onNodeClick?.(node.data.originalNode);
    },
    [onNodeClick]
  );

  // Empty state
  if (!nodes.length) {
    return (
      <div
        className={cn(
          'flex items-center justify-center h-[500px] bg-slate-50 rounded-lg border',
          className
        )}
      >
        <p className="text-muted-foreground">Nenhum no na arvore</p>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <div className="w-full h-[500px] bg-slate-50 rounded-lg border overflow-hidden">
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={true}
          minZoom={0.2}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#e2e8f0" gap={16} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <span>Vencedor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-blue-500" />
          <span>Ativo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-slate-400" />
          <span>Dominado</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-red-500" />
          <span>Falhou</span>
        </div>
      </div>
    </div>
  );
}
