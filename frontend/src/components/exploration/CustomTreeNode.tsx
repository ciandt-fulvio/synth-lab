/**
 * CustomTreeNode component for react-d3-tree.
 *
 * Renders a custom node with status-based colors and click handling.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US2)
 *   - Library: https://bkrem.github.io/react-d3-tree/docs/
 */

import type { CustomNodeElementProps } from 'react-d3-tree';
import type { ScenarioNode, NodeStatus } from '@/types/exploration';
import { NODE_STATUS_COLORS } from '@/types/exploration';

interface TreeNodeDatum {
  name: string;
  attributes?: {
    action?: string;
    status: NodeStatus;
  };
  __nodeData: ScenarioNode;
}

interface CustomTreeNodeProps extends Omit<CustomNodeElementProps, 'nodeDatum'> {
  nodeDatum: TreeNodeDatum;
  onNodeClick?: (node: ScenarioNode) => void;
  selectedNodeId?: string | null;
  winningPathNodeIds?: Set<string>;
}

const NODE_RADIUS = 24;
const SELECTED_RING_RADIUS = 30;

export function CustomTreeNode({
  nodeDatum,
  onNodeClick,
  selectedNodeId,
  winningPathNodeIds,
}: CustomTreeNodeProps) {
  const status = nodeDatum.attributes?.status || 'active';
  const isSelected = selectedNodeId === nodeDatum.__nodeData.id;
  const isOnWinningPath = winningPathNodeIds?.has(nodeDatum.__nodeData.id);
  const isRoot = nodeDatum.__nodeData.parent_id === null;

  // Get fill color based on status
  const fillColor = NODE_STATUS_COLORS[status];

  // Stroke for winning path highlight
  const strokeColor = isOnWinningPath ? '#fbbf24' : 'transparent'; // amber-400
  const strokeWidth = isOnWinningPath ? 4 : 0;

  const handleClick = () => {
    onNodeClick?.(nodeDatum.__nodeData);
  };

  return (
    <g onClick={handleClick} style={{ cursor: 'pointer' }}>
      {/* Selection ring */}
      {isSelected && (
        <circle
          r={SELECTED_RING_RADIUS}
          fill="none"
          stroke="#6366f1"
          strokeWidth={3}
          strokeDasharray="4 2"
          className="animate-pulse"
        />
      )}

      {/* Winning path highlight ring */}
      {isOnWinningPath && !isSelected && (
        <circle
          r={NODE_RADIUS + 4}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
        />
      )}

      {/* Main node circle */}
      <circle
        r={NODE_RADIUS}
        fill={fillColor}
        stroke="white"
        strokeWidth={2}
        className="transition-all duration-200 hover:opacity-80"
      />

      {/* Node label (success rate) - text outline for readability */}
      <text
        dy=".35em"
        textAnchor="middle"
        fill="white"
        fontSize={14}
        fontWeight={700}
        stroke="rgba(0,0,0,0.4)"
        strokeWidth={2.5}
        paintOrder="stroke fill"
        style={{ pointerEvents: 'none' }}
      >
        {nodeDatum.name}
      </text>

      {/* Root indicator */}
      {isRoot && (
        <text
          dy={-NODE_RADIUS - 10}
          textAnchor="middle"
          fill="#1e293b"
          fontSize={12}
          fontWeight={700}
          style={{ pointerEvents: 'none' }}
        >
          Baseline
        </text>
      )}

      {/* Action label (truncated) */}
      {nodeDatum.attributes?.action && (
        <text
          dy={NODE_RADIUS + 18}
          textAnchor="middle"
          fill="#475569"
          fontSize={11}
          fontWeight={600}
          style={{ pointerEvents: 'none' }}
        >
          {nodeDatum.attributes.action}
        </text>
      )}
    </g>
  );
}
