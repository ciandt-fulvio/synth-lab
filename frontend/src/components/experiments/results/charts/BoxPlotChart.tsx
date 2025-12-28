// frontend/src/components/experiments/results/charts/BoxPlotChart.tsx
// Box plot showing distribution of an attribute across outcome groups

import type { BoxPlotChart as BoxPlotData } from '@/types/simulation';

interface BoxPlotChartProps {
  data: BoxPlotData;
}

const OUTCOME_COLORS = {
  success: { bg: 'bg-green-100', border: 'border-green-400', fill: 'fill-green-400' },
  failed: { bg: 'bg-red-100', border: 'border-red-400', fill: 'fill-red-400' },
  did_not_try: { bg: 'bg-slate-100', border: 'border-slate-400', fill: 'fill-slate-400' },
} as const;

const OUTCOME_LABELS = {
  success: 'Sucesso',
  failed: 'Falhou',
  did_not_try: 'Não Tentou',
} as const;

interface BoxPlotSVGProps {
  stats: {
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
  };
  color: keyof typeof OUTCOME_COLORS;
  scale: { min: number; max: number };
  width: number;
  height: number;
}

function BoxPlotSVG({ stats, color, scale, width, height }: BoxPlotSVGProps) {
  const colors = OUTCOME_COLORS[color];
  const padding = 20;
  const plotWidth = width - padding * 2;
  const boxHeight = height * 0.4;
  const centerY = height / 2;

  // Scale function
  const scaleX = (value: number) => {
    const range = scale.max - scale.min;
    if (range === 0) return padding + plotWidth / 2;
    return padding + ((value - scale.min) / range) * plotWidth;
  };

  const minX = scaleX(stats.min);
  const q1X = scaleX(stats.q1);
  const medianX = scaleX(stats.median);
  const q3X = scaleX(stats.q3);
  const maxX = scaleX(stats.max);

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Whisker line (min to max) */}
      <line
        x1={minX}
        y1={centerY}
        x2={maxX}
        y2={centerY}
        className={`stroke-current ${colors.fill.replace('fill-', 'text-')}`}
        strokeWidth={2}
      />

      {/* Min whisker cap */}
      <line
        x1={minX}
        y1={centerY - boxHeight / 3}
        x2={minX}
        y2={centerY + boxHeight / 3}
        className={`stroke-current ${colors.fill.replace('fill-', 'text-')}`}
        strokeWidth={2}
      />

      {/* Max whisker cap */}
      <line
        x1={maxX}
        y1={centerY - boxHeight / 3}
        x2={maxX}
        y2={centerY + boxHeight / 3}
        className={`stroke-current ${colors.fill.replace('fill-', 'text-')}`}
        strokeWidth={2}
      />

      {/* Box (Q1 to Q3) */}
      <rect
        x={q1X}
        y={centerY - boxHeight / 2}
        width={q3X - q1X}
        height={boxHeight}
        className={`${colors.bg} ${colors.border} stroke-2`}
        rx={4}
      />

      {/* Median line */}
      <line
        x1={medianX}
        y1={centerY - boxHeight / 2}
        x2={medianX}
        y2={centerY + boxHeight / 2}
        className={`stroke-current ${colors.fill.replace('fill-', 'text-')}`}
        strokeWidth={3}
      />
    </svg>
  );
}

export function BoxPlotChart({ data }: BoxPlotChartProps) {
  const { groups, attribute, global_stats } = data;

  // Calculate global scale for consistent comparison
  const scale = {
    min: global_stats.min,
    max: global_stats.max,
  };

  return (
    <div className="space-y-6">
      {/* Attribute label */}
      <div className="text-center">
        <span className="text-sm font-medium text-slate-600">
          Distribuição de: {attribute.replace(/_/g, ' ').replace(/mean/g, '').trim()}
        </span>
      </div>

      {/* Box plots */}
      <div className="space-y-4">
        {Object.entries(groups).map(([outcome, stats]) => (
          <div key={outcome} className="flex items-center gap-4">
            {/* Label */}
            <div className="w-24 text-right">
              <span className="text-sm font-medium text-slate-700">
                {OUTCOME_LABELS[outcome as keyof typeof OUTCOME_LABELS] || outcome}
              </span>
            </div>

            {/* Box plot */}
            <div className="flex-1">
              <BoxPlotSVG
                stats={stats}
                color={outcome as keyof typeof OUTCOME_COLORS}
                scale={scale}
                width={400}
                height={60}
              />
            </div>

            {/* Stats */}
            <div className="w-32 text-xs text-slate-500 space-y-0.5">
              <div>Mediana: {stats.median.toFixed(2)}</div>
              <div>IQR: {(stats.q3 - stats.q1).toFixed(2)}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Scale reference */}
      <div className="flex items-center justify-center gap-4 text-xs text-slate-500">
        <span>Min: {scale.min.toFixed(2)}</span>
        <div className="w-40 h-1 bg-gradient-to-r from-slate-200 via-slate-300 to-slate-400 rounded" />
        <span>Max: {scale.max.toFixed(2)}</span>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        {Object.entries(OUTCOME_LABELS).map(([key, label]) => {
          const colors = OUTCOME_COLORS[key as keyof typeof OUTCOME_COLORS];
          return (
            <div key={key} className="flex items-center gap-2">
              <div className={`w-4 h-4 rounded ${colors.bg} ${colors.border} border`} />
              <span className="text-slate-600">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
