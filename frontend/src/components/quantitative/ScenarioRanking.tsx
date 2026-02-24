/**
 * ScenarioRanking component.
 *
 * Sortable table of all batch scenarios with product values and stats.
 * Highlights top 3 (green), bottom 3 (red), and median (amber).
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (ScenarioRunResult)
 */

import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronRight } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import type { ScenarioRunResult } from '@/types/quantitative-analysis';

interface ScenarioRankingProps {
  scenarios: ScenarioRunResult[];
}

const CALIBRATION_SHORT: Record<string, string> = {
  low: 'B',
  medium: 'M',
  high: 'A',
};

const CALIBRATION_CELL_COLORS: Record<string, string> = {
  low: 'text-red-600 bg-red-50',
  medium: 'text-amber-600 bg-amber-50',
  high: 'text-emerald-600 bg-emerald-50',
};

type SortField = 'mean' | 'p10' | 'p90' | 'std';

export function ScenarioRanking({ scenarios }: ScenarioRankingProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sortField, setSortField] = useState<SortField>('mean');
  const [sortAsc, setSortAsc] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Collect product node names
  const productNodes = useMemo(() => {
    const nodes = new Set<string>();
    for (const s of scenarios) {
      for (const key of Object.keys(s.product_values)) {
        nodes.add(key);
      }
    }
    return Array.from(nodes);
  }, [scenarios]);

  const sorted = useMemo(() => {
    const arr = [...scenarios];
    arr.sort((a, b) => {
      const va = a.stats[sortField];
      const vb = b.stats[sortField];
      return sortAsc ? va - vb : vb - va;
    });
    return arr;
  }, [scenarios, sortField, sortAsc]);

  // Highlight sets
  const topIds = new Set(sorted.slice(0, 3).map((s) => s.run_id));
  const bottomIds = new Set(sorted.slice(-3).map((s) => s.run_id));
  const medianIdx = Math.floor(sorted.length / 2);
  const medianId = sorted[medianIdx]?.run_id;

  const displayed = showAll ? sorted : sorted.slice(0, 20);

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  }

  function SortHeader({ field, label }: { field: SortField; label: string }) {
    const active = sortField === field;
    return (
      <th
        className="text-right py-2 px-2 text-xs font-medium text-slate-500 cursor-pointer hover:text-slate-700 select-none whitespace-nowrap"
        onClick={() => handleSort(field)}
      >
        <span className="inline-flex items-center gap-0.5">
          {label}
          {active && (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
        </span>
      </th>
    );
  }

  function rowClass(runId: string): string {
    if (topIds.has(runId)) return 'bg-emerald-50/60';
    if (bottomIds.has(runId)) return 'bg-red-50/60';
    if (runId === medianId) return 'bg-amber-50/60';
    return '';
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full flex items-center justify-between px-4 py-3 bg-slate-50/80 hover:bg-slate-100 transition-colors text-left"
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              Ranking de Cenários
              <span className="text-xs font-normal text-slate-400">({scenarios.length} cenários)</span>
            </span>
            {isOpen
              ? <ChevronDown className="w-4 h-4 text-slate-400" />
              : <ChevronRight className="w-4 h-4 text-slate-400" />
            }
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
        <div className="bg-white px-4 pt-3 pb-4">
      <p className="text-sm text-slate-500 mb-3">
        Ordenados por {sortField.toUpperCase()}.
        <span className="ml-2 inline-block w-2 h-2 rounded-full bg-emerald-400 align-middle" /> Top 3
        <span className="ml-2 inline-block w-2 h-2 rounded-full bg-red-400 align-middle" /> Bottom 3
        <span className="ml-2 inline-block w-2 h-2 rounded-full bg-amber-400 align-middle" /> Mediana
      </p>

      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left py-2 px-2 text-xs font-medium text-slate-500 w-8">#</th>
              {productNodes.map((node) => (
                <th key={node} className="text-center py-2 px-2 text-xs font-medium text-slate-500 max-w-[100px] truncate" title={node}>
                  {node}
                </th>
              ))}
              <SortHeader field="mean" label="Média" />
              <SortHeader field="p10" label="P10" />
              <SortHeader field="p90" label="P90" />
              <SortHeader field="std" label="σ" />
            </tr>
          </thead>
          <tbody>
            {displayed.map((scenario, i) => (
              <tr key={scenario.run_id} className={`border-b border-slate-100 ${rowClass(scenario.run_id)}`}>
                <td className="py-1.5 px-2 text-xs text-slate-400 font-mono">{i + 1}</td>
                {productNodes.map((node) => {
                  const level = scenario.product_values[node] ?? '–';
                  const colorClass = CALIBRATION_CELL_COLORS[level] ?? '';
                  return (
                    <td key={node} className="py-1.5 px-2 text-center">
                      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${colorClass}`}>
                        {CALIBRATION_SHORT[level] ?? level}
                      </span>
                    </td>
                  );
                })}
                <td className="py-1.5 px-2 text-right font-mono font-semibold text-slate-800">
                  {scenario.stats.mean.toFixed(1)}%
                </td>
                <td className="py-1.5 px-2 text-right font-mono text-slate-600">
                  {scenario.stats.p10.toFixed(1)}%
                </td>
                <td className="py-1.5 px-2 text-right font-mono text-slate-600">
                  {scenario.stats.p90.toFixed(1)}%
                </td>
                <td className="py-1.5 px-2 text-right font-mono text-slate-500">
                  {scenario.stats.std.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!showAll && sorted.length > 20 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          Mostrar todos os {sorted.length} cenários
        </button>
      )}
        </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
