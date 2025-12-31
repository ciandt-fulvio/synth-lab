/**
 * CustomTreeNode component for react-d3-tree.
 *
 * Renders a custom node using foreignObject + HTML for crisp text rendering.
 * Shows success rate prominently with short action label below.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US2)
 *   - Library: https://bkrem.github.io/react-d3-tree/docs/
 */

import type { CustomNodeElementProps } from 'react-d3-tree';
import type { ScenarioNode, NodeStatus } from '@/types/exploration';
import { cn } from '@/lib/utils';

interface TreeNodeDatum {
  name: string;
  attributes?: {
    action?: string;
    shortAction?: string;
    status: NodeStatus;
  };
  __nodeData: ScenarioNode;
}

interface CustomTreeNodeProps extends Omit<CustomNodeElementProps, 'nodeDatum'> {
  nodeDatum: TreeNodeDatum;
  onNodeClick?: (node: ScenarioNode) => void;
  selectedNodeId?: string | null;
  winningPathNodeIds?: Set<string>;
  bestNodeId?: string | null;
}

// Card dimensions
const CARD_WIDTH = 140;
const CARD_HEIGHT = 70;

// Status-based styles for the card
const STATUS_STYLES: Record<NodeStatus, { border: string; bg: string; text: string; actionText: string }> = {
  winner: {
    border: 'border-green-500',
    bg: 'bg-green-50',
    text: 'text-slate-800',
    actionText: 'text-slate-500',
  },
  active: {
    border: 'border-blue-500',
    bg: 'bg-blue-50',
    text: 'text-slate-800',
    actionText: 'text-slate-500',
  },
  dominated: {
    border: 'border-slate-300',
    bg: 'bg-slate-50',
    text: 'text-slate-400',
    actionText: 'text-slate-300',
  },
  expansion_failed: {
    border: 'border-red-400',
    bg: 'bg-red-50',
    text: 'text-slate-800',
    actionText: 'text-slate-500',
  },
};

export function CustomTreeNode({
  nodeDatum,
  onNodeClick,
  selectedNodeId,
  winningPathNodeIds,
  bestNodeId,
}: CustomTreeNodeProps) {
  const status = nodeDatum.attributes?.status || 'active';
  const isSelected = selectedNodeId === nodeDatum.__nodeData.id;
  const isOnWinningPath = winningPathNodeIds?.has(nodeDatum.__nodeData.id);
  const isRoot = nodeDatum.__nodeData.parent_id === null;
  const isBestNode = bestNodeId === nodeDatum.__nodeData.id && status !== 'winner';

  const styles = STATUS_STYLES[status];
  const shortAction = nodeDatum.attributes?.shortAction;

  const handleClick = () => {
    onNodeClick?.(nodeDatum.__nodeData);
  };

  return (
    <g onClick={handleClick} style={{ cursor: 'pointer' }}>
      {/* foreignObject for HTML card */}
      <foreignObject
        width={CARD_WIDTH}
        height={CARD_HEIGHT}
        x={-CARD_WIDTH / 2}
        y={-CARD_HEIGHT / 2}
      >
        <div
          className={cn(
            'h-full w-full rounded-xl px-3 py-2 border-2',
            'font-sans text-center transition-all duration-200',
            'hover:shadow-lg hover:scale-[1.02]',
            'flex flex-col items-center justify-center relative',
            styles.border,
            styles.bg,
            // Selection: dashed border + stronger shadow
            isSelected && 'border-indigo-500 border-dashed shadow-lg shadow-indigo-200',
            // Winning path: amber border
            isOnWinningPath && !isSelected && 'border-amber-400 border-[3px] shadow-md shadow-amber-100',
            // Best node: amber border + glow
            isBestNode && !isSelected && !isOnWinningPath && 'border-amber-500 border-[3px] shadow-lg shadow-amber-200',
            // Normal shadow for non-special nodes
            !isSelected && !isOnWinningPath && !isBestNode && 'shadow-md'
          )}
        >
          {/* Success rate - main metric */}
          <div className={cn(
            'font-bold leading-none',
            styles.text,
            // Best node: blue text, slightly larger
            isBestNode ? 'text-[22px] text-blue-600' : 'text-xl'
          )}>
            {nodeDatum.name}
          </div>

          {/* Short action label or "Baseline" for root */}
          {isRoot ? (
            <div className={cn('text-xs font-semibold mt-1', styles.actionText)}>
              Baseline
            </div>
          ) : shortAction ? (
            <div
              className={cn('text-xs mt-1 truncate w-full px-1', styles.actionText)}
              title={nodeDatum.__nodeData.action_applied || undefined}
            >
              {shortAction}
            </div>
          ) : (
            // Fallback to truncated action if no short_action
            nodeDatum.attributes?.action && (
              <div
                className={cn('text-xs mt-1 truncate w-full px-1', styles.actionText)}
                title={nodeDatum.__nodeData.action_applied || undefined}
              >
                {nodeDatum.attributes.action}
              </div>
            )
          )}
        </div>
      </foreignObject>
    </g>
  );
}
