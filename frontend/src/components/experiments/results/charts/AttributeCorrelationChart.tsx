// frontend/src/components/experiments/results/charts/AttributeCorrelationChart.tsx
// Horizontal bar chart showing correlation of synth attributes with outcomes

import type { AttributeCorrelationChart as ChartData } from '@/types/simulation';

interface AttributeCorrelationChartProps {
  data: ChartData;
}

// Color based on correlation strength and direction
function getBarColor(value: number, isSignificant: boolean): string {
  if (!isSignificant) {
    return 'rgb(203, 213, 225)'; // slate-300 for non-significant
  }

  const absValue = Math.abs(value);

  if (value > 0) {
    // Positive correlations: blue scale
    if (absValue > 0.5) return 'rgb(37, 99, 235)';   // blue-600
    if (absValue > 0.3) return 'rgb(59, 130, 246)';  // blue-500
    return 'rgb(96, 165, 250)';                       // blue-400
  } else {
    // Negative correlations: red scale
    if (absValue > 0.5) return 'rgb(220, 38, 38)';   // red-600
    if (absValue > 0.3) return 'rgb(239, 68, 68)';   // red-500
    return 'rgb(248, 113, 113)';                      // red-400
  }
}

// Format correlation value for display
function formatCorrelation(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(0)}%`;
}

export function AttributeCorrelationChart({ data }: AttributeCorrelationChartProps) {
  const { correlations, total_synths } = data;

  if (correlations.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        Nenhum dado de correlação disponível
      </div>
    );
  }

  // Find max absolute correlation for scaling
  const maxAbsCorr = Math.max(
    ...correlations.flatMap(c => [
      Math.abs(c.correlation_attempt),
      Math.abs(c.correlation_success),
    ])
  );
  const scale = maxAbsCorr > 0 ? 1 / maxAbsCorr : 1;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Ordenado por correlação com sucesso (mais forte → mais fraca)</span>
        <span>{total_synths} synths analisados</span>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-blue-500" />
          <span className="text-slate-600">Correlação positiva</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-red-500" />
          <span className="text-slate-600">Correlação negativa</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-slate-300" />
          <span className="text-slate-600">Não significativo (p ≥ 0.05)</span>
        </div>
      </div>

      {/* Chart */}
      <div className="space-y-3">
        {/* Column headers */}
        <div className="grid grid-cols-[200px_1fr_1fr] gap-4 text-xs font-medium text-slate-600 border-b border-slate-200 pb-2">
          <div>Atributo</div>
          <div className="text-center">Correlação com Tentativa</div>
          <div className="text-center">Correlação com Sucesso</div>
        </div>

        {/* Rows */}
        {correlations.map((corr) => (
          <div
            key={corr.attribute}
            className="grid grid-cols-[200px_1fr_1fr] gap-4 items-center"
          >
            {/* Attribute label */}
            <div className="text-sm font-medium text-slate-700 truncate" title={corr.attribute}>
              {corr.attribute_label}
            </div>

            {/* Attempt correlation bar */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-6 bg-slate-100 rounded relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-px h-full bg-slate-300" style={{ left: '50%' }} />
                </div>
                <div
                  className="absolute h-full rounded transition-all duration-300"
                  style={{
                    width: `${Math.abs(corr.correlation_attempt) * scale * 50}%`,
                    left: corr.correlation_attempt >= 0 ? '50%' : undefined,
                    right: corr.correlation_attempt < 0 ? '50%' : undefined,
                    backgroundColor: getBarColor(corr.correlation_attempt, corr.is_significant_attempt),
                  }}
                />
              </div>
              <span
                className={`text-xs font-mono w-12 text-right ${
                  corr.is_significant_attempt ? 'text-slate-700' : 'text-slate-400'
                }`}
              >
                {formatCorrelation(corr.correlation_attempt)}
              </span>
            </div>

            {/* Success correlation bar */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-6 bg-slate-100 rounded relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-px h-full bg-slate-300" style={{ left: '50%' }} />
                </div>
                <div
                  className="absolute h-full rounded transition-all duration-300"
                  style={{
                    width: `${Math.abs(corr.correlation_success) * scale * 50}%`,
                    left: corr.correlation_success >= 0 ? '50%' : undefined,
                    right: corr.correlation_success < 0 ? '50%' : undefined,
                    backgroundColor: getBarColor(corr.correlation_success, corr.is_significant_success),
                  }}
                />
              </div>
              <span
                className={`text-xs font-mono w-12 text-right ${
                  corr.is_significant_success ? 'text-slate-700' : 'text-slate-400'
                }`}
              >
                {formatCorrelation(corr.correlation_success)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Interpretation guide */}
      <div className="mt-4 p-3 bg-slate-50 rounded-lg">
        <p className="text-xs text-slate-600">
          <strong>Como interpretar:</strong> Valores positivos indicam que aumentos no atributo
          estão associados a maior tentativa/sucesso. Valores negativos indicam o oposto.
          Barras cinzas não são estatisticamente significativas (p ≥ 0.05).
        </p>
      </div>
    </div>
  );
}
