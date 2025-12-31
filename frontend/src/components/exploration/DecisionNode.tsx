/**
 * DecisionNode component for React Flow.
 *
 * HTML-based node with status colors and typography.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md
 *   - Library: https://reactflow.dev/learn/customization/custom-nodes
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import type { DecisionNodeData } from '@/types/exploration';
import { cn } from '@/lib/utils';
import { Trophy } from 'lucide-react';

// Base styles by status
const STATUS_STYLES: Record<string, string> = {
  winner: 'border-l-green-600 bg-green-100',
  active: 'border-l-blue-500 bg-blue-50/90',
  dominated: 'border-l-slate-500 bg-slate-100/90',
  expansion_failed: 'border-l-red-500 bg-red-50/90',
};

// Value text colors by status
const STATUS_VALUE_COLORS: Record<string, string> = {
  winner: 'text-green-700',
  active: 'text-blue-700',
  dominated: 'text-slate-700',
  expansion_failed: 'text-red-700',
};

// Label text colors by status (for better contrast on dominated)
const STATUS_LABEL_COLORS: Record<string, string> = {
  winner: 'text-slate-800',
  active: 'text-slate-800',
  dominated: 'text-slate-700',
  expansion_failed: 'text-slate-800',
};

export const DecisionNode = memo(function DecisionNode({
  data,
  selected,
}: NodeProps<DecisionNodeData>) {
  // Use short label if available, otherwise use truncated full label
  const displayLabel = data.shortLabel || data.label;

  // Determine if this is a highlighted node (winner or best)
  const isHighlighted = data.isWinner || data.isBest;

  return (
    <>
      {/* Target handle (left side) - hidden for root node */}
      {!data.isRoot && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-2 !h-2 !bg-slate-400 !border-0"
        />
      )}

      <div
        className={cn(
          'w-[200px] px-3 py-2.5 rounded-lg shadow-sm',
          'bg-white/95 backdrop-blur-sm',
          'transition-all duration-200',
          // Border width: thicker for highlighted nodes
          isHighlighted ? 'border-l-[6px]' : 'border-l-4',
          STATUS_STYLES[data.status],
          // Enhanced shadow for highlighted nodes
          isHighlighted && 'shadow-md',
          // Winner gets extra emphasis
          data.isWinner && 'ring-2 ring-green-400 ring-offset-1',
          // Selection style
          selected && 'ring-2 ring-indigo-500 ring-offset-2 shadow-lg'
        )}
      >
        {/* Winner badge with trophy */}
        {data.isWinner && (
          <div className="flex items-center gap-1 mb-1">
            <Trophy className="h-3.5 w-3.5 text-amber-500" />
            <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wide">
              Vencedor
            </span>
          </div>
        )}

        {/* Root indicator */}
        {data.isRoot && (
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-0.5">
            Baseline
          </div>
        )}

        {/* Best indicator (only if not winner and not root) */}
        {data.isBest && !data.isWinner && !data.isRoot && (
          <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wide mb-0.5">
            Melhor Taxa
          </div>
        )}

        {/* Label (action) */}
        <div
          className={cn(
            'text-sm font-semibold leading-tight',
            !data.isRoot && 'line-clamp-2',
            STATUS_LABEL_COLORS[data.status]
          )}
          title={data.label}
        >
          {data.isRoot ? 'Cenario Inicial' : displayLabel}
        </div>

        {/* Value (success rate) */}
        {data.value !== null && (
          <div
            className={cn(
              'mt-1 text-xl font-bold tabular-nums',
              STATUS_VALUE_COLORS[data.status],
              // Extra bold for highlighted
              isHighlighted && 'text-2xl'
            )}
          >
            {data.value.toFixed(0)}%
          </div>
        )}
      </div>

      {/* Source handle (right side) */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-slate-400 !border-0"
      />
    </>
  );
});
