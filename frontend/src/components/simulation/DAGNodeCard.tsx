/**
 * DAGNodeCard - Compact causal DAG node with hover details.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import type { Variable } from '@/types/causal-dag';

interface DAGNodeData {
  variable: Variable;
  isSelected?: boolean;
  onEdit?: (variable: Variable) => void;
  onDelete?: (variableName: string) => void;
}

/**
 * Get colors by scope only - user-level vs world-level.
 */
function getVariableColors(scope: string) {
  if (scope === 'user') {
    // User-level: darker indigo
    return {
      bg: '#4f46e5', // indigo-600
      border: '#4338ca', // indigo-700
      text: 'text-white',
    };
  } else {
    // World-level: lighter indigo
    return {
      bg: '#818cf8', // indigo-400
      border: '#6366f1', // indigo-500
      text: 'text-white',
    };
  }
}

function DAGNodeCardComponent({ data, selected }: NodeProps<DAGNodeData>) {
  const { variable } = data;
  const isSelected = selected || data.isSelected;
  const colors = getVariableColors(variable.scope);

  return (
    <div
      className={`
        group relative min-w-[200px] max-w-[260px] rounded-lg border-2 shadow-lg transition-all
        ${isSelected ? 'ring-2 ring-yellow-400 ring-offset-2 scale-105' : 'hover:scale-105'}
      `}
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
      }}
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

        {/* Type label - larger and clearer */}
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

      {/* Hover tooltip - ALWAYS on top with portal-like behavior */}
      {variable.description && (
        <div
          className="absolute left-full top-0 ml-4 hidden group-hover:block pointer-events-none"
          style={{ zIndex: 9999 }}
        >
          <div className="bg-slate-900 text-white text-sm rounded-lg shadow-2xl p-4 max-w-sm border-2 border-slate-700">
            <div className="font-bold mb-2 text-base text-white">{variable.label}</div>
            <p className="text-slate-200 leading-relaxed">{variable.description}</p>
            {variable.unit && (
              <div className="mt-3 pt-3 border-t border-slate-700 text-slate-400 text-xs">
                <span className="font-semibold">Unit:</span> {variable.unit}
              </div>
            )}
            <div className="mt-2 text-[10px] text-slate-500 uppercase tracking-wide">
              {variable.scope}-level • {variable.variable_type}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const DAGNodeCard = memo(DAGNodeCardComponent);
