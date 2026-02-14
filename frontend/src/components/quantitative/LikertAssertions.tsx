/**
 * LikertAssertions component.
 *
 * Displays a card per edge with header and 5 radio options.
 * Selected state is highlighted. onChange calls debounced save via hook.
 * Shows answer progress "5/8 respondidas".
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Spec: specs/042-quantitative-analysis/spec.md
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { CheckCircle2, Circle, ChevronDown, ChevronUp } from 'lucide-react';
import type { CausalEdge } from '@/types/quantitative-analysis';

interface LikertAssertionsProps {
  edges: CausalEdge[];
  activeEdgeId?: string | null;
  onEdgeFocus?: (edgeId: string | null) => void;
  onSelectionsChange: (selections: Record<string, number>) => void;
}

/** Debounce utility for batching selection saves. */
function useDebouncedCallback<T extends (...args: unknown[]) => void>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => callbackRef.current(...args), delay);
    },
    [delay]
  ) as T;
}

export function LikertAssertions({
  edges,
  activeEdgeId,
  onEdgeFocus,
  onSelectionsChange,
}: LikertAssertionsProps) {
  const [localSelections, setLocalSelections] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    for (const edge of edges) {
      if (edge.selected_option !== null) {
        initial[edge.id] = edge.selected_option;
      }
    }
    return initial;
  });

  const [expandedEdge, setExpandedEdge] = useState<string | null>(activeEdgeId ?? null);

  // Sync expanded edge with activeEdgeId prop
  useEffect(() => {
    if (activeEdgeId) {
      setExpandedEdge(activeEdgeId);
    }
  }, [activeEdgeId]);

  const debouncedSave = useDebouncedCallback(
    (selections: Record<string, number>) => {
      onSelectionsChange(selections);
    },
    500
  );

  const handleSelect = (edgeId: string, optionIndex: number) => {
    const updated = { ...localSelections, [edgeId]: optionIndex };
    setLocalSelections(updated);
    debouncedSave(updated);
  };

  const answeredCount = Object.keys(localSelections).length;
  const totalEdges = edges.length;

  return (
    <div className="space-y-3">
      {/* Progress */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-700">
          Premissas Causais
        </span>
        <span className={`text-sm font-medium ${answeredCount === totalEdges ? 'text-emerald-600' : 'text-slate-500'}`}>
          {answeredCount}/{totalEdges} respondidas
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-100 rounded-full h-1.5 mb-4">
        <div
          className="bg-gradient-to-r from-violet-500 to-indigo-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${totalEdges > 0 ? (answeredCount / totalEdges) * 100 : 0}%` }}
        />
      </div>

      {/* Edge cards */}
      {edges.map((edge) => {
        const isExpanded = expandedEdge === edge.id;
        const isActive = activeEdgeId === edge.id;
        const selectedOption = localSelections[edge.id] ?? null;
        const isAnswered = selectedOption !== null;

        return (
          <div
            key={edge.id}
            className={`rounded-lg border transition-all duration-200 ${
              isActive
                ? 'border-violet-300 bg-violet-50/50 shadow-sm'
                : isAnswered
                  ? 'border-emerald-200 bg-white'
                  : 'border-slate-200 bg-white'
            }`}
            onMouseEnter={() => onEdgeFocus?.(edge.id)}
            onMouseLeave={() => onEdgeFocus?.(null)}
          >
            {/* Header */}
            <button
              type="button"
              className="w-full flex items-center gap-3 px-4 py-3 text-left"
              onClick={() => setExpandedEdge(isExpanded ? null : edge.id)}
            >
              {isAnswered ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              ) : (
                <Circle className="h-4 w-4 text-slate-300 flex-shrink-0" />
              )}
              <span className="text-sm font-medium text-slate-700 flex-1">
                {edge.header}
              </span>
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-slate-400 flex-shrink-0" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />
              )}
            </button>

            {/* Options (collapsible) */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-2">
                {edge.options.map((option, idx) => {
                  const isSelected = selectedOption === idx;
                  const isDefault = edge.default_option === idx;

                  return (
                    <button
                      key={idx}
                      type="button"
                      className={`w-full text-left px-3 py-2.5 rounded-md border transition-all duration-150 text-sm ${
                        isSelected
                          ? 'border-violet-400 bg-violet-50 text-violet-800 font-medium'
                          : 'border-slate-150 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                      onClick={() => handleSelect(edge.id, idx)}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                            isSelected
                              ? 'border-violet-500'
                              : 'border-slate-300'
                          }`}
                        >
                          {isSelected && (
                            <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                          )}
                        </div>
                        <span>{option.text}</span>
                        {isDefault && !isSelected && (
                          <span className="ml-auto text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                            padrão
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
