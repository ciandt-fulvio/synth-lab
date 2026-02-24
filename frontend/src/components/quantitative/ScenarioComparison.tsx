/**
 * ScenarioComparison component.
 *
 * Shows worst, median, and best scenarios side by side.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (ScenarioRunResult)
 */

import { useState } from 'react';
import { TrendingUp, Minus, TrendingDown, ChevronDown, ChevronRight } from 'lucide-react';
import type { ScenarioRunResult, CausalNodeMeta } from '@/types/quantitative-analysis';

interface ScenarioComparisonProps {
  scenarios: ScenarioRunResult[];
  nodeMetadata: Record<string, CausalNodeMeta> | null;
}

const CALIBRATION_LABELS: Record<string, string> = {
  low: 'Baixo',
  medium: 'Médio',
  high: 'Alto',
};

interface CardConfig {
  label: string;
  icon: typeof TrendingUp;
  gradient: string;
  border: string;
  iconBg: string;
  iconColor: string;
  accentColor: string;
  chipClass: string;
  calibrationColors: Record<string, string>;
}

const CALIBRATION_DOT: Record<string, string> = {
  low: 'bg-red-400',
  medium: 'bg-amber-400',
  high: 'bg-emerald-500',
};

const CARD_CONFIGS: CardConfig[] = [
  {
    label: 'Pior Cenário',
    icon: TrendingDown,
    gradient: 'from-red-50 to-rose-50',
    border: 'border-red-200',
    iconBg: 'bg-red-100',
    iconColor: 'text-red-500',
    accentColor: 'text-red-600',
    chipClass: '',
    calibrationColors: {},
  },
  {
    label: 'Cenário Mediano',
    icon: Minus,
    gradient: 'from-amber-50 to-yellow-50',
    border: 'border-amber-200',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    accentColor: 'text-amber-700',
    chipClass: '',
    calibrationColors: {},
  },
  {
    label: 'Melhor Cenário',
    icon: TrendingUp,
    gradient: 'from-emerald-50 to-teal-50',
    border: 'border-emerald-200',
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    accentColor: 'text-emerald-700',
    chipClass: '',
    calibrationColors: {},
  },
];

export function ScenarioComparison({ scenarios, nodeMetadata }: ScenarioComparisonProps) {
  const [attributesOpen, setAttributesOpen] = useState(false);

  if (scenarios.length === 0) return null;

  const productNodes = nodeMetadata
    ? Object.entries(nodeMetadata).filter(([, meta]) => meta.node_type === 'product')
    : [];

  const sorted = [...scenarios].sort((a, b) => b.stats.mean - a.stats.mean);
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];
  const median = sorted[Math.floor(sorted.length / 2)];
  const picks = [worst, median, best];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="text-base font-semibold text-slate-800 mb-3">Comparativo de Cenários</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {picks.map((scenario, i) => {
          const config = CARD_CONFIGS[i];
          const Icon = config.icon;
          return (
            <div
              key={scenario.run_id}
              className={`rounded-xl border ${config.border} bg-gradient-to-br ${config.gradient} p-5 flex flex-col gap-4`}
            >
              {/* Header */}
              <div className="flex items-center gap-2.5">
                <div className={`w-8 h-8 rounded-lg ${config.iconBg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${config.iconColor}`} />
                </div>
                <span className="text-sm font-semibold text-slate-700">{config.label}</span>
              </div>

              {/* Hero number */}
              <div>
                <p className={`text-5xl font-black tracking-tight ${config.accentColor}`}>
                  {scenario.stats.mean.toFixed(1)}
                  <span className="text-2xl font-bold ml-0.5">%</span>
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  IC 80%: {scenario.stats.p10.toFixed(1)}–{scenario.stats.p90.toFixed(1)}%
                </p>
              </div>

              {/* Calibration chips */}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(scenario.product_values).map(([node, level]) => {
                  const dot = CALIBRATION_DOT[level] ?? 'bg-slate-400';
                  return (
                    <span
                      key={node}
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-white/70 text-slate-700 border border-slate-200/80 shadow-sm"
                    >
                      <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                      {node}: {CALIBRATION_LABELS[level] ?? level}
                    </span>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {productNodes.length > 0 && (
        <div className="mt-4 border border-violet-100 rounded-xl overflow-hidden shadow-sm">
          <button
            type="button"
            onClick={() => setAttributesOpen((o) => !o)}
            className="w-full flex items-center justify-between px-4 py-3 bg-violet-50/60 hover:bg-violet-50 transition-colors text-left"
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-violet-700">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
              Atributos do Produto
              <span className="text-xs font-normal text-violet-400">({productNodes.length})</span>
            </span>
            {attributesOpen
              ? <ChevronDown className="w-4 h-4 text-violet-400" />
              : <ChevronRight className="w-4 h-4 text-violet-400" />
            }
          </button>

          {attributesOpen && (
            <div className="divide-y divide-slate-100 bg-white">
              {productNodes.map(([key, meta]) => (
                <div key={key} className="px-4 py-3 flex gap-3">
                  <div className="mt-1 w-1.5 h-1.5 rounded-full bg-violet-300 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">{meta.name}</p>
                    {meta.description && (
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{meta.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
