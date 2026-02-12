/**
 * SensitivityHistograms component.
 *
 * Renders a 3-column grid of bar histograms for the 9 synth sensitivities.
 * Each histogram uses 0.05-width buckets, Y-axis = count, bars flush together.
 * Below each chart a short description explains the sensitivity.
 *
 * References:
 *   - Types: src/types/synthGroup.ts (SensitivityStats)
 *   - Labels: src/lib/observable-labels.ts
 *   - Charts: recharts v2.15
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { formatFeatureName } from '@/lib/observable-labels';
import type { SensitivityStats, HistogramData } from '@/types/synthGroup';

const SENSITIVITY_ORDER = [
  'risk_aversion',
  'social_dependency',
  'institutional_trust_level',
  'habit_plasticity',
  'friction_tolerance',
  'pragmatism',
  'digital_capability',
  'motor_ability',
  'subject_domain',
];

/** Short descriptions for each sensitivity (0 = low, 1 = high). */
const SENSITIVITY_DESCRIPTIONS: Record<string, string> = {
  risk_aversion:
    'Tendência a evitar incertezas. Valores altos indicam perfil conservador; baixos, abertura a novidades.',
  social_dependency:
    'Influência do grupo nas decisões. Perto de 1, segue a maioria; perto de 0, decide de forma independente.',
  institutional_trust_level:
    'Grau de confiança em instituições formais (governo, bancos, empresas). Baixo indica ceticismo.',
  habit_plasticity:
    'Facilidade de abandonar rotinas existentes. Valores altos significam adaptação rápida a mudanças.',
  friction_tolerance:
    'Paciência com etapas, formulários e obstáculos. Valores baixos indicam abandono diante de fricção.',
  pragmatism:
    'Foco em resultado prático vs. experiência. Perto de 1, prioriza utilidade; perto de 0, valoriza estética.',
  digital_capability:
    'Fluência com tecnologia e interfaces digitais. Derivado de idade, escolaridade e contexto socioeconômico.',
  motor_ability:
    'Capacidade motora, derivada de condições de deficiência física. Valor 1.0 = sem limitações.',
  subject_domain:
    'Conhecimento prévio sobre o domínio do produto. Leigos ficam perto de 0, especialistas perto de 1.',
};

const BAR_COLOR = '#4f46e5'; // indigo-600
const MEAN_COLOR = '#dc2626'; // red-600

interface SensitivityHistogramsProps {
  data: SensitivityStats;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      name: string;
      count: number;
    };
  }>;
}

function HistogramTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const { name, count } = payload[0].payload;
  const upper = (parseFloat(name) + 0.05).toFixed(2);
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md px-3 py-2 text-xs">
      <p className="text-slate-600 mb-0.5">{name} – {upper}</p>
      <p className="font-semibold text-slate-900">{count} synths</p>
    </div>
  );
}

function SensitivityChart({ name, hist }: { name: string; hist: HistogramData }) {
  // Show every 4th tick label to avoid crowding (0.00, 0.20, 0.40, 0.60, 0.80)
  const tickFormatter = (value: string, index: number) => {
    return index % 4 === 0 ? value : '';
  };

  const description = SENSITIVITY_DESCRIPTIONS[name];

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 flex flex-col">
      <h4 className="text-sm font-medium text-slate-700 mb-1 truncate">
        {formatFeatureName(name)}
      </h4>
      <p className="text-xs text-slate-400 mb-2">
        Média: {hist.mean.toFixed(2)} | Desvio: {hist.std_dev.toFixed(2)}
      </p>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={hist.buckets}
            barCategoryGap={0}
            barGap={0}
            margin={{ top: 5, right: 5, bottom: 0, left: -10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 9 }}
              tickFormatter={tickFormatter}
              interval={0}
            />
            <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
            <Tooltip content={<HistogramTooltip />} />
            <ReferenceLine
              x={hist.buckets.findIndex((b) => parseFloat(b.label) <= hist.mean && hist.mean < parseFloat(b.label) + 0.05) >= 0
                ? hist.buckets[hist.buckets.findIndex((b) => parseFloat(b.label) <= hist.mean && hist.mean < parseFloat(b.label) + 0.05)].label
                : undefined}
              stroke={MEAN_COLOR}
              strokeDasharray="4 2"
              strokeWidth={1.5}
              label={{ value: 'μ', position: 'top', fontSize: 10, fill: MEAN_COLOR }}
            />
            <Bar dataKey="count" fill={BAR_COLOR} radius={0} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {description && (
        <p className="text-[11px] leading-relaxed text-slate-400 mt-2 border-t border-slate-100 pt-2">
          {description}
        </p>
      )}
    </div>
  );
}

export function SensitivityHistograms({ data }: SensitivityHistogramsProps) {
  // Order sensitivities deterministically
  const keys = SENSITIVITY_ORDER.filter((k) => k in data.distributions);
  for (const k of Object.keys(data.distributions)) {
    if (!keys.includes(k)) keys.push(k);
  }

  if (keys.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-slate-400">
        Nenhuma sensibilidade encontrada neste grupo.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-slate-900">Sensibilidades</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {keys.map((key) => (
          <SensitivityChart key={key} name={key} hist={data.distributions[key]} />
        ))}
      </div>
    </div>
  );
}
