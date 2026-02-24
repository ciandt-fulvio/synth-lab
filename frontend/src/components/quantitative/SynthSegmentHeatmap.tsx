/**
 * SynthSegmentHeatmap component.
 *
 * 3×3 heatmap showing average adoption % for each combination of the two
 * synth attributes with highest Pearson |r|. Cells colored green → red.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (SynthAttributeInsightsResponse)
 *   - Hook: useSynthAttributeInsights
 */

import { Loader2 } from 'lucide-react';
import { useSynthAttributeInsights } from '@/hooks/use-quantitative-analysis';

interface SynthSegmentHeatmapProps {
  experimentId: string;
}

const BIN_LABELS = ['Baixo', 'Médio', 'Alto'] as const;

/** Map 0–100% adoption to a tailwind-compatible hex color green → amber → red */
function adoptionColor(pct: number, min: number, max: number): string {
  const range = max - min || 1;
  const t = Math.max(0, Math.min(1, (pct - min) / range)); // 0 = worst, 1 = best
  // Interpolate: red(239,68,68) → amber(245,158,11) → emerald(16,185,129)
  if (t < 0.5) {
    const u = t / 0.5;
    const r = Math.round(239 + (245 - 239) * u);
    const g = Math.round(68 + (158 - 68) * u);
    const b = Math.round(68 + (11 - 68) * u);
    return `rgb(${r},${g},${b})`;
  } else {
    const u = (t - 0.5) / 0.5;
    const r = Math.round(245 + (16 - 245) * u);
    const g = Math.round(158 + (185 - 158) * u);
    const b = Math.round(11 + (129 - 11) * u);
    return `rgb(${r},${g},${b})`;
  }
}

export function SynthSegmentHeatmap({ experimentId }: SynthSegmentHeatmapProps) {
  const { data, isLoading } = useSynthAttributeInsights(experimentId);

  if (isLoading) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 text-violet-500 mx-auto animate-spin" />
      </div>
    );
  }

  if (!data || data.heatmap.length === 0) return null;

  // Build lookup: (row_bin, col_bin) → cell
  const cellMap = new Map(
    data.heatmap.map((c) => [`${c.row_bin}|${c.col_bin}`, c])
  );

  const allPcts = data.heatmap.map((c) => c.adoption_pct);
  const minPct = Math.min(...allPcts);
  const maxPct = Math.max(...allPcts);

  return (
    <div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">
        Segmentação por Atributo
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        Adoção média (%) por combinação dos dois atributos mais correlacionados.{' '}
        <span className="font-medium text-slate-600">
          Linhas: {data.heatmap_row_label} · Colunas: {data.heatmap_col_label}
        </span>
      </p>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              {/* Top-left corner cell */}
              <th className="p-2 text-xs text-slate-400 font-medium text-left w-24">
                {data.heatmap_row_label} ↓ / {data.heatmap_col_label} →
              </th>
              {BIN_LABELS.map((colBin) => (
                <th
                  key={colBin}
                  className="p-2 text-xs font-semibold text-slate-600 text-center"
                >
                  {colBin}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {BIN_LABELS.map((rowBin) => (
              <tr key={rowBin}>
                <td className="p-2 text-xs font-semibold text-slate-600 text-right pr-3 w-24">
                  {rowBin}
                </td>
                {BIN_LABELS.map((colBin) => {
                  const cell = cellMap.get(`${rowBin}|${colBin}`);
                  const pct = cell?.adoption_pct ?? 0;
                  const count = cell?.count ?? 0;
                  const bg = adoptionColor(pct, minPct, maxPct);
                  const textColor = pct > (minPct + maxPct) / 2 ? '#fff' : '#1e293b';
                  return (
                    <td
                      key={colBin}
                      className="p-0 text-center border border-white"
                      style={{ minWidth: 80 }}
                    >
                      <div
                        className="flex flex-col items-center justify-center py-3 px-2 rounded"
                        style={{ backgroundColor: bg }}
                      >
                        <span
                          className="text-lg font-black leading-none"
                          style={{ color: textColor }}
                        >
                          {pct.toFixed(1)}%
                        </span>
                        <span
                          className="text-[10px] mt-0.5 opacity-75"
                          style={{ color: textColor }}
                        >
                          {count} synths
                        </span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Color scale legend */}
      <div className="flex items-center gap-2 mt-3">
        <span className="text-[10px] text-slate-400">Baixa adoção</span>
        <div
          className="flex-1 h-2 rounded-full"
          style={{
            background: 'linear-gradient(to right, rgb(239,68,68), rgb(245,158,11), rgb(16,185,129))',
          }}
        />
        <span className="text-[10px] text-slate-400">Alta adoção</span>
      </div>
    </div>
  );
}
