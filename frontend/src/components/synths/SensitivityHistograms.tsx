/**
 * SensitivityHistograms component.
 *
 * Renders a 2×2 grid of distribution histograms for the 4 synth sensitivities.
 * Each histogram uses 0.05-width buckets with gradient fills and an elegant
 * mean reference line. Descriptions available via info tooltips.
 *
 * Design: Editorial data-journalism aesthetic (FiveThirtyEight / The Economist).
 * Compact layout with refined typography and teal accent palette.
 *
 * References:
 *   - Types: src/types/synthGroup.ts (SensitivityStats)
 *   - Labels: src/lib/observable-labels.ts
 *   - Charts: recharts v2.15
 */

import { Info } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { formatFeatureName } from '@/lib/observable-labels';
import type { SensitivityStats, HistogramData } from '@/types/synthGroup';

const SENSITIVITY_ORDER = [
  'risk_aversion',
  'institutional_trust_level',
  'friction_tolerance',
  'digital_capability',
];

/** Descriptions shown in info tooltips. */
const SENSITIVITY_DESCRIPTIONS: Record<string, string> = {
  risk_aversion:
    'Tendência a evitar incertezas. Valores altos indicam perfil conservador; baixos, abertura a novidades.',
  institutional_trust_level:
    'Grau de confiança em instituições formais (governo, bancos, empresas). Baixo indica ceticismo.',
  friction_tolerance:
    'Paciência com etapas, formulários e obstáculos. Valores baixos indicam abandono diante de fricção.',
  digital_capability:
    'Fluência com tecnologia e interfaces digitais. Derivado de idade, escolaridade e contexto socioeconômico.',
};

/** Teal gradient stops for bar fill based on position in [0,1] range. */
function getBarFill(label: string): string {
  const v = parseFloat(label);
  if (v < 0.3) return '#99f6e4';   // teal-200
  if (v < 0.5) return '#5eead4';   // teal-300
  if (v < 0.7) return '#2dd4bf';   // teal-400
  return '#14b8a6';                 // teal-500
}

interface SensitivityHistogramsProps {
  data: SensitivityStats;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      label: string;
      count: number;
      percentage: number;
    };
  }>;
}

function HistogramTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const lower = d.label;
  const upper = (parseFloat(lower) + 0.05).toFixed(2);
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-xs">
      <p className="text-slate-300 tabular-nums">{lower} – {upper}</p>
      <p className="font-semibold text-white mt-0.5">
        {d.count} synths
        <span className="font-normal text-slate-400 ml-1">
          ({d.percentage.toFixed(1)}%)
        </span>
      </p>
    </div>
  );
}

function SensitivityChart({ name, hist }: { name: string; hist: HistogramData }) {
  const tickFormatter = (_value: string, index: number) => {
    if (index === 0) return '0';
    if (index === 10) return '.50';
    if (index === 19) return '1';
    return '';
  };

  const description = SENSITIVITY_DESCRIPTIONS[name];

  // Find the bucket index for mean reference line
  const meanBucketLabel = hist.buckets.find(
    (b) => parseFloat(b.label) <= hist.mean && hist.mean < parseFloat(b.label) + 0.05
  )?.label;

  return (
    <div className="relative bg-white rounded-lg border border-slate-200/80 px-4 pt-3.5 pb-3 hover:border-slate-300 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <h4 className="text-[13px] font-semibold text-slate-800 tracking-tight truncate">
            {formatFeatureName(name)}
          </h4>
          {description && (
            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    className="text-slate-300 hover:text-slate-500 transition-colors shrink-0"
                    aria-label={`Info: ${formatFeatureName(name)}`}
                  >
                    <Info className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  className="max-w-[240px] bg-slate-800 text-slate-100 border-slate-700"
                >
                  <p className="text-xs leading-relaxed">{description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <div className="flex items-baseline gap-2 shrink-0 ml-2">
          <span className="text-[11px] text-slate-400 tabular-nums">
            μ&thinsp;=&thinsp;
            <span className="font-semibold text-slate-600">
              {hist.mean.toFixed(2)}
            </span>
          </span>
          <span className="text-[11px] text-slate-400 tabular-nums">
            σ&thinsp;=&thinsp;{hist.std_dev.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[130px] -mx-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={hist.buckets}
            barCategoryGap={0}
            barGap={0}
            margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#f1f5f9"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 9, fill: '#94a3b8' }}
              tickFormatter={tickFormatter}
              interval={0}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 9, fill: '#94a3b8' }}
              allowDecimals={false}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <RechartsTooltip
              content={<HistogramTooltip />}
              cursor={{ fill: 'rgba(15, 23, 42, 0.04)' }}
            />
            {meanBucketLabel && (
              <ReferenceLine
                x={meanBucketLabel}
                stroke="#334155"
                strokeWidth={1.5}
                strokeDasharray="3 2"
                label={{
                  value: 'μ',
                  position: 'top',
                  fontSize: 9,
                  fontWeight: 600,
                  fill: '#334155',
                }}
              />
            )}
            <Bar dataKey="count" radius={[1, 1, 0, 0]}>
              {hist.buckets.map((entry) => (
                <Cell key={entry.label} fill={getBarFill(entry.label)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function SensitivityHistograms({ data }: SensitivityHistogramsProps) {
  const keys = SENSITIVITY_ORDER.filter((k) => k in data.distributions);

  if (keys.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-slate-400">
        Nenhuma sensibilidade encontrada neste grupo.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Section header */}
      <div className="flex items-baseline justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Sensibilidades</h3>
        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-[2px] border-t-2 border-dashed border-slate-500" />
            Média (μ)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-2.5 rounded-sm bg-gradient-to-r from-teal-200 to-teal-500" />
            Distribuição
          </span>
        </div>
      </div>

      {/* 2×2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {keys.map((key) => (
          <SensitivityChart
            key={key}
            name={key}
            hist={data.distributions[key]}
          />
        ))}
      </div>
    </div>
  );
}
