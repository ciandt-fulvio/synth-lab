/**
 * LikertAssertions component.
 *
 * Compact card list for reviewing pre-filled causal edge assumptions.
 * All edges start with LLM defaults pre-selected. Users click to expand
 * and optionally adjust. Cards that diverge from default show "ajustado" badge.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Spec: specs/042-quantitative-analysis/spec.md
 */

import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { CausalEdge } from '@/types/quantitative-analysis';

interface LikertAssertionsProps {
  edges: CausalEdge[];
  activeEdgeId?: string | null;
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
  onSelectionsChange,
}: LikertAssertionsProps) {
  // Pre-fill every edge with selected_option or default_option
  const [localSelections, setLocalSelections] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    for (const edge of edges) {
      initial[edge.id] = edge.selected_option ?? edge.default_option;
    }
    return initial;
  });

  // Track which defaults each edge started with
  const defaults = useMemo(() => {
    const d: Record<string, number> = {};
    for (const edge of edges) {
      d[edge.id] = edge.default_option;
    }
    return d;
  }, [edges]);

  // Track edges where user diverged from LLM default
  const modifiedEdges = useMemo(() => {
    const modified = new Set<string>();
    for (const edge of edges) {
      const current = localSelections[edge.id];
      if (current !== undefined && current !== defaults[edge.id]) {
        modified.add(edge.id);
      }
    }
    return modified;
  }, [edges, localSelections, defaults]);

  const [expandedEdge, setExpandedEdge] = useState<string | null>(activeEdgeId ?? null);

  // Sync expanded edge with activeEdgeId prop (DAG click)
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

  const modifiedCount = modifiedEdges.size;
  const totalEdges = edges.length;

  return (
    <div className="space-y-2">
      {/* Progress header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-700">
          Premissas Causais
        </span>
        <span className="text-xs text-slate-500">
          {modifiedCount > 0
            ? `${modifiedCount}/${totalEdges} ajustadas`
            : `${totalEdges} premissas com valores sugeridos`}
        </span>
      </div>

      {/* Edge cards */}
      {edges.map((edge) => {
        const isExpanded = expandedEdge === edge.id;
        const isActive = activeEdgeId === edge.id;
        const selectedOption = localSelections[edge.id] ?? edge.default_option;
        const isModified = modifiedEdges.has(edge.id);
        const selectedText = edge.options[selectedOption]?.text ?? '';

        return (
          <div
            key={edge.id}
            className={`rounded-lg border transition-all duration-200 ${
              isExpanded
                ? 'border-l-4 border-l-violet-500 border-y-slate-200 border-r-slate-200 bg-violet-50/30'
                : isActive
                  ? 'border-violet-300 bg-violet-50/30'
                  : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            {/* Header — always visible */}
            <button
              type="button"
              className="w-full flex items-start gap-2 px-4 py-3 text-left"
              onClick={() => setExpandedEdge(isExpanded ? null : edge.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700">
                    {edge.header}
                  </span>
                  {isModified && (
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-100 text-violet-700">
                      ajustado
                    </span>
                  )}
                </div>
                {/* Inline preview of selected option (collapsed only) */}
                {!isExpanded && (
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {selectedText}
                  </p>
                )}
              </div>
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" />
              )}
            </button>

            {/* Options (collapsible) */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-2">
                {edge.options.map((option, idx) => {
                  const isSelected = selectedOption === idx;

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
