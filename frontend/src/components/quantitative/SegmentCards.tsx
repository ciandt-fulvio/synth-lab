/**
 * SegmentCards component.
 *
 * Displays adoption rates segmented by age, income, and education.
 * Each dimension shows buckets with rate, count, and color gradient.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (Segments, SegmentResult)
 *   - Spec: specs/042-quantitative-analysis/spec.md
 */

import { Users, TrendingUp, GraduationCap, Wallet } from 'lucide-react';
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

function getRateColor(rate: number): string {
  if (rate >= 60) return 'bg-emerald-50 border-emerald-200 text-emerald-700';
  if (rate >= 40) return 'bg-blue-50 border-blue-200 text-blue-700';
  if (rate >= 20) return 'bg-amber-50 border-amber-200 text-amber-700';
  return 'bg-red-50 border-red-200 text-red-700';
}

function getRateBarColor(rate: number): string {
  if (rate >= 60) return 'bg-emerald-500';
  if (rate >= 40) return 'bg-blue-500';
  if (rate >= 20) return 'bg-amber-500';
  return 'bg-red-500';
}

export function SegmentCards({ segments, interpretation }: SegmentCardsProps) {
  return (
    <div className="space-y-5">
      {DIMENSION_CONFIG.map(({ key, label, icon: Icon }) => {
        const dimension = segments[key];
        if (!dimension) return null;

        return (
          <div key={key}>
            <div className="flex items-center gap-2 mb-3">
              <Icon className="w-4 h-4 text-slate-500" />
              <h4 className="text-sm font-medium text-slate-700">{label}</h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {Object.entries(dimension).map(([bucket, result]) => (
                <SegmentCard
                  key={bucket}
                  bucket={BUCKET_LABELS[bucket] ?? bucket}
                  rate={result.rate}
                  count={result.count}
                />
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

function SegmentCard({ bucket, rate, count }: { bucket: string; rate: number; count: number }) {
  return (
    <div className={`rounded-lg border p-3 ${getRateColor(rate)}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium opacity-80">{bucket}</span>
        <TrendingUp className="w-3.5 h-3.5 opacity-60" />
      </div>
      <p className="text-2xl font-bold">{rate.toFixed(1)}%</p>
      <div className="mt-2">
        <div className="w-full h-1.5 rounded-full bg-white/50">
          <div
            className={`h-1.5 rounded-full ${getRateBarColor(rate)}`}
            style={{ width: `${Math.min(rate, 100)}%` }}
          />
        </div>
        <p className="text-xs mt-1 opacity-70">{count} synths</p>
      </div>
    </div>
  );
}
