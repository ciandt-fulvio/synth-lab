/**
 * DAGNodeCard - Compact causal DAG node with click-to-edit.
 *
 * Replaces hover tooltips with click-to-open NodeDetailSheet.
 * Color saturation varies by relevance level.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import type { Variable } from '@/types/causal-dag';

import type { Relevance } from '@/types/hypothesis';

interface DAGNodeData {
  variable: Variable;
  relevance?: Relevance;
  isSelected?: boolean;
  onEdit?: (variable: Variable) => void;
  onEditNode?: (variable: Variable) => void;
  onDelete?: (variableName: string) => void;
}

/**
 * Saturation multiplier by relevance level.
 * high=100%, medium=70%, low=40%
 */
const RELEVANCE_SATURATION: Record<string, number> = {
  high: 1.0,
  medium: 0.7,
  low: 0.4,
};

/**
 * Get HSL node color based on scope and relevance.
 *
 * Base colors (full saturation):
 * - user: HSL(263, 84%, 58%) — violet
 * - world: HSL(189, 95%, 42%) — cyan
 *
 * Saturation is multiplied by relevance factor.
 */
export function getNodeColor(scope: string, relevance: string = 'high'): { bg: string; border: string; text: string } {
  const satMult = RELEVANCE_SATURATION[relevance] ?? 1.0;

  if (scope === 'user') {
    const sat = Math.round(84 * satMult);
    return {
      bg: `hsl(263, ${sat}%, 58%)`,
      border: `hsl(263, ${sat}%, 48%)`,
      text: 'text-white',
    };
  } else {
    const sat = Math.round(95 * satMult);
    return {
      bg: `hsl(189, ${sat}%, 42%)`,
      border: `hsl(189, ${sat}%, 32%)`,
      text: 'text-white',
    };
  }
}

function DAGNodeCardComponent({ data, selected }: NodeProps<DAGNodeData>) {
  const { variable, relevance } = data;
  const isSelected = selected || data.isSelected;
  const colors = getNodeColor(variable.scope, relevance || 'high');

  const handleClick = () => {
    data.onEditNode?.(variable);
  };

  return (
    <div
      className={`
        relative min-w-[200px] max-w-[260px] rounded-lg border-2 shadow-lg transition-all cursor-pointer
        ${isSelected ? 'ring-2 ring-yellow-400 ring-offset-2 scale-105' : 'hover:scale-105'}
      `}
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
      }}
      onClick={handleClick}
    >
      {/* Input handle - LEFT side for LR layout */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-white !border-2 !border-slate-400"
      />

      {/* Content */}
      <div className="px-4 py-3">
        <p className={`text-base font-semibold leading-tight ${colors.text}`}>
          {variable.label}
        </p>

        {/* Type label */}
        <div className="flex items-center gap-1.5 mt-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              variable.scope === 'user' ? 'bg-white' : 'bg-white/50'
            }`}
            title={variable.scope === 'user' ? 'User-level' : 'World-level'}
          />
          <span className="text-xs font-medium text-white/80 uppercase tracking-wide">
            {variable.variable_type}
          </span>
        </div>
      </div>

      {/* Output handle - RIGHT side for LR layout */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-white !border-2 !border-slate-400"
      />

      {/* Delete button - shows on hover when editable */}
      {data.onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`Remover variável "${variable.label}"?`)) {
              data.onDelete?.(variable.name);
            }
          }}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center shadow-lg"
          title="Remover variável"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

export const DAGNodeCard = memo(DAGNodeCardComponent);
