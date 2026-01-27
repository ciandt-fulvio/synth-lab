/**
 * DAGNodeCard - Compact causal DAG node with hover details.
 */

import { memo, useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
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
    // User-level: violet
    return {
      bg: '#7c3aed', // violet-600
      border: '#6d28d9', // violet-700
      text: 'text-white',
    };
  } else {
    // World-level: cyan
    return {
      bg: '#06b6d4', // cyan-500
      border: '#0891b2', // cyan-600
      text: 'text-white',
    };
  }
}

function DAGNodeCardComponent({ data, selected }: NodeProps<DAGNodeData>) {
  const { variable } = data;
  const isSelected = selected || data.isSelected;
  const colors = getVariableColors(variable.scope);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showTooltip && cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      setTooltipPosition({
        x: rect.right + 16, // 16px margin
        y: rect.top + rect.height * 0.6,
      });
    }
  }, [showTooltip]);

  return (
    <>
      <div
        ref={cardRef}
        className={`
          relative min-w-[200px] max-w-[260px] rounded-lg border-2 shadow-lg transition-all
          ${isSelected ? 'ring-2 ring-yellow-400 ring-offset-2 scale-105' : 'hover:scale-105'}
        `}
        style={{
          backgroundColor: colors.bg,
          borderColor: colors.border,
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
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
    </div>

    {/* Tooltip rendered via portal - always on top */}
    {showTooltip && variable.description && createPortal(
      <div
        className="fixed pointer-events-none"
        style={{
          left: tooltipPosition.x,
          top: tooltipPosition.y,
          zIndex: 99999,
        }}
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
      </div>,
      document.body
    )}
  </>
  );
}

export const DAGNodeCard = memo(DAGNodeCardComponent);
