/**
 * LikertAssertions component.
 *
 * Compact card list for reviewing pre-filled causal node premissas.
 * Each interaction and outcome node has 5 Likert options that determine
 * the node's weight in the simulation. Users click to expand and
 * optionally adjust. Cards that diverge from default show "ajustado" badge.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Spec: specs/042-quantitative-analysis/spec.md
 */

import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '@/components/ui/tooltip';
import type { CausalNodeMeta, LikertOption } from '@/types/quantitative-analysis';

/** A calibratable node (interaction or outcome) with premissa options. */
export interface CalibratableNode {
  name: string;
  nodeType: string;
  header: string;
  description: string;
  options: LikertOption[];
  defaultOption: number;
  selectedOption: number | null;
}

interface LikertAssertionsProps {
  nodes: CalibratableNode[];
  activeNodeName?: string | null;
  onNodeActivate?: (nodeName: string | null) => void;
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

/**
 * Build CalibratableNode list from node_metadata.
 * Sorted by DAG topology order (nodeOrder), with outcome always last.
 */
export function buildCalibratableNodes(
  nodeMetadata: Record<string, CausalNodeMeta> | null,
  nodeOrder?: string[],
): CalibratableNode[] {
  if (!nodeMetadata) return [];

  const orderIndex = new Map<string, number>();
  if (nodeOrder) {
    nodeOrder.forEach((name, idx) => orderIndex.set(name, idx));
  }

  return Object.values(nodeMetadata)
    .filter(
      (meta) =>
        (meta.node_type === 'interaction' || meta.node_type === 'outcome') &&
        meta.options &&
        meta.options.length > 0
    )
    .map((meta) => ({
      name: meta.name,
      nodeType: meta.node_type,
      header: meta.header ?? `Peso de ${meta.name}`,
      description: meta.description ?? '',
      options: meta.options!,
      defaultOption: meta.default_option ?? 2,
      selectedOption: meta.selected_option ?? null,
    }))
    .sort((a, b) => {
      // Outcome always last
      if (a.nodeType === 'outcome' && b.nodeType !== 'outcome') return 1;
      if (b.nodeType === 'outcome' && a.nodeType !== 'outcome') return -1;
      // Otherwise preserve DAG topology order
      const ia = orderIndex.get(a.name) ?? Infinity;
      const ib = orderIndex.get(b.name) ?? Infinity;
      return ia - ib;
    });
}

export function LikertAssertions({
  nodes,
  activeNodeName,
  onNodeActivate,
  onSelectionsChange,
}: LikertAssertionsProps) {
  // Pre-fill every node with selected_option or default_option
  const [localSelections, setLocalSelections] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    for (const node of nodes) {
      initial[node.name] = node.selectedOption ?? node.defaultOption;
    }
    return initial;
  });

  // Refs for scrolling into view
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Track which defaults each node started with
  const defaults = useMemo(() => {
    const d: Record<string, number> = {};
    for (const node of nodes) {
      d[node.name] = node.defaultOption;
    }
    return d;
  }, [nodes]);

  // Track nodes where user diverged from LLM default
  const modifiedNodes = useMemo(() => {
    const modified = new Set<string>();
    for (const node of nodes) {
      const current = localSelections[node.name];
      if (current !== undefined && current !== defaults[node.name]) {
        modified.add(node.name);
      }
    }
    return modified;
  }, [nodes, localSelections, defaults]);

  const [expandedNode, setExpandedNode] = useState<string | null>(activeNodeName ?? null);

  // Sync expanded node with activeNodeName prop + scroll into view
  useEffect(() => {
    if (activeNodeName) {
      setExpandedNode(activeNodeName);
      // Scroll the card into view after a short delay for DOM update
      setTimeout(() => {
        const el = cardRefs.current[activeNodeName];
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 50);
    }
  }, [activeNodeName]);

  const debouncedSave = useDebouncedCallback(
    (selections: Record<string, number>) => {
      onSelectionsChange(selections);
    },
    500
  );

  const handleSelect = (nodeName: string, optionIndex: number) => {
    const updated = { ...localSelections, [nodeName]: optionIndex };
    setLocalSelections(updated);
    debouncedSave(updated);
  };

  const modifiedCount = modifiedNodes.size;
  const totalNodes = nodes.length;

  return (
    <div className="space-y-2">
      {/* Progress header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-700">
          Premissas Causais
        </span>
        <span className="text-xs text-slate-500">
          {modifiedCount > 0
            ? `${modifiedCount}/${totalNodes} ajustadas`
            : `${totalNodes} premissas com valores sugeridos`}
        </span>
      </div>

      {/* Node cards */}
      {nodes.map((node) => {
        const isExpanded = expandedNode === node.name;
        const isActive = activeNodeName === node.name;
        const selectedOption = localSelections[node.name] ?? node.defaultOption;
        const isModified = modifiedNodes.has(node.name);
        const selectedText = node.options[selectedOption]?.text ?? '';

        const typeLabel = node.nodeType === 'outcome' ? 'Resultado' : 'Interação';
        const typeBg = node.nodeType === 'outcome' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700';

        return (
          <div
            key={node.name}
            ref={(el) => { cardRefs.current[node.name] = el; }}
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
              onClick={() => {
                const next = isExpanded ? null : node.name;
                setExpandedNode(next);
                onNodeActivate?.(next);
              }}
            >
              <div className="flex-1 min-w-0">
                {/* Title row: node name + sugerido/ajustado badge + chevron */}
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700">
                    {node.name}
                  </span>
                  {isModified ? (
                    <TooltipProvider delayDuration={200}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-100 text-violet-700 cursor-default">
                            ajustado
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Valor diferente do sugerido pela IA</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : (
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500">
                      sugerido
                    </span>
                  )}
                </div>
                {/* Type badge below */}
                <div className="mt-1">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${typeBg}`}>
                    {typeLabel}
                  </span>
                </div>
                {/* Description / selected preview */}
                {!isExpanded && (
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {selectedText}
                  </p>
                )}
                {isExpanded && node.description && (
                  <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                    {node.description}
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
                {node.options.map((option, idx) => {
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
                      onClick={() => handleSelect(node.name, idx)}
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
