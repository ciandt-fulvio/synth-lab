/**
 * SegmentCards component.
 *
 * Displays adoption rates segmented by age, income, and education.
 * Cards are ordered from lowest to highest category within each dimension.
 * Only the card with the highest rate in each dimension gets a green border.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (Segments, SegmentResult)
 *   - Style: matches StatCard from DistributionChart (gray border, bold number)
 */

import { Users, GraduationCap, Wallet } from 'lucide-react';
import type { Segments, Interpretation } from '@/types/quantitative-analysis';

interface SegmentCardsProps {
  segments: Segments;
  interpretation?: Interpretation;
}

const DIMENSION_CONFIG: {
  key: keyof Segments;
  label: string;
  icon: typeof Users;
}[] = [
  { key: 'age', label: 'Idade', icon: Users },
  { key: 'income', label: 'Renda', icon: Wallet },
  { key: 'education', label: 'Escolaridade', icon: GraduationCap },
];

const BUCKET_LABELS: Record<string, string> = {
  '18-29': '18–29 anos',
  '30-49': '30–49 anos',
  '50+': '50+ anos',
  'baixa': 'Baixa',
  'media': 'Média',
  'alta': 'Alta',
};

/** Sort order within each dimension (lowest → highest category). */
const BUCKET_ORDER: Record<string, number> = {
  // Age
  '18-29': 0,
  '30-49': 1,
  '50+': 2,
  // Income & Education
  'baixa': 0,
  'media': 1,
  'alta': 2,
};

function SpreadBadge({ spreadPp }: { spreadPp: number }) {
  if (spreadPp < 5) {
    return (
      <span className="ml-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
        Δ {spreadPp.toFixed(1)}pp
      </span>
    );
  }
  if (spreadPp <= 15) {
    return (
      <span className="ml-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">
        Δ {spreadPp.toFixed(1)}pp
      </span>
    );
  }
  return (
    <span className="ml-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600">
      Δ {spreadPp.toFixed(1)}pp
    </span>
  );
}

export function SegmentCards({ segments, interpretation }: SegmentCardsProps) {
  return (
    <div className="space-y-5">
      {DIMENSION_CONFIG.map(({ key, label, icon: Icon }) => {
        const dimension = segments[key];
        if (!dimension) return null;

        const entries = Object.entries(dimension).sort(
          ([a], [b]) => (BUCKET_ORDER[a] ?? 99) - (BUCKET_ORDER[b] ?? 99)
        );

        const rates = entries.map(([, r]) => r.rate);
        const maxRate = Math.max(...rates);
        const minRate = Math.min(...rates);
        const spreadPp = maxRate - minRate;

        // Only highlight winner card when spread is actionable (≥ 5pp)
        const showWinner = spreadPp >= 5;

        return (
          <div key={key}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className="w-4 h-4 text-slate-500" />
              <h4 className="text-sm font-medium text-slate-700">{label}</h4>
              <SpreadBadge spreadPp={spreadPp} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {entries.map(([bucket, result]) => (
                <div
                  key={bucket}
                  className={`rounded-lg border px-3 py-2 ${
                    showWinner && result.rate === maxRate
                      ? 'border-emerald-400 bg-white'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <p className="text-xs text-slate-500">{BUCKET_LABELS[bucket] ?? bucket}</p>
                  <p className="text-lg font-semibold text-slate-800">{result.rate.toFixed(1)}%</p>
                  <p className="text-[11px] text-slate-400">{result.count} synths</p>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* AI Interpretation */}
      {interpretation && (
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Interpretação — Segmentos
          </p>
          <p className="text-sm text-slate-700 leading-relaxed">
            {interpretation.ai_text || interpretation.raw_text}
          </p>
        </div>
      )}
    </div>
  );
}
