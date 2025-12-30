// frontend/src/components/experiments/results/charts/FailureHeatmap.tsx
// Professional heatmap visualization for failure rate analysis

import { useMemo } from 'react';
import type { FailureHeatmapChart } from '@/types/simulation';
import { OBSERVABLE_LABELS } from '@/lib/observable-labels';

interface FailureHeatmapProps {
  data: FailureHeatmapChart;
}

function getLabel(attr: string): { short: string; full: string } {
  const fullName = OBSERVABLE_LABELS[attr];
  if (fullName) {
    // Create short version from full name (first word or abbreviated)
    const words = fullName.split(' ');
    const shortName = words.length > 2 ? words.slice(0, 2).join(' ') : fullName;
    return { short: shortName, full: fullName };
  }
  return { short: attr, full: attr };
}

// Parse bin string to get bounds: "0.0-0.2" -> [0.0, 0.2]
function parseBinBounds(bin: string): [number, number] {
  const match = bin.match(/^([\d.]+)-([\d.]+)$/);
  if (match) {
    return [parseFloat(match[1]), parseFloat(match[2])];
  }
  return [0, 0];
}

// Format bin for display: "0.0-0.2" -> "0-20%"
function formatBinLabel(bin: string): string {
  const [start, end] = parseBinBounds(bin);
  return `${Math.round(start * 100)}-${Math.round(end * 100)}%`;
}

// Perceptually uniform color scale (blue → white → coral/red)
// Uses relative scaling based on actual data range for better contrast
function getHeatmapColor(value: number, minVal: number, maxVal: number): string {
  // Normalize to 0-1 based on actual data range (with some padding)
  const range = maxVal - minVal;
  const normalized = range > 0 ? (value - minVal) / range : 0.5;

  // Color scale: deep blue (low) → slate (mid) → coral/red (high)
  // This ensures variation is visible even when all values are "low"
  if (normalized < 0.25) {
    // Deep blue to light blue
    return `hsl(210, ${70 - normalized * 40}%, ${45 + normalized * 30}%)`;
  } else if (normalized < 0.5) {
    // Light blue to slate/neutral
    const t = (normalized - 0.25) / 0.25;
    return `hsl(${210 - t * 30}, ${30 - t * 20}%, ${60 + t * 15}%)`;
  } else if (normalized < 0.75) {
    // Slate to warm orange
    const t = (normalized - 0.5) / 0.25;
    return `hsl(${180 - t * 150}, ${10 + t * 50}%, ${75 - t * 15}%)`;
  } else {
    // Orange to coral/red
    const t = (normalized - 0.75) / 0.25;
    return `hsl(${30 - t * 25}, ${60 + t * 25}%, ${60 - t * 15}%)`;
  }
}

// Get text color based on background luminance
function getTextColor(value: number, minVal: number, maxVal: number): string {
  const range = maxVal - minVal;
  const normalized = range > 0 ? (value - minVal) / range : 0.5;
  // Dark text for light backgrounds, light text for dark backgrounds
  return normalized < 0.3 || normalized > 0.85 ? 'white' : 'rgba(15, 23, 42, 0.9)';
}

export function FailureHeatmap({ data }: FailureHeatmapProps) {
  const { cells, x_axis, y_axis } = data;

  // Process cells data
  const { xLabels, yLabels, cellMap, stats } = useMemo(() => {
    const xSet = new Set<string>();
    const ySet = new Set<string>();
    const map = new Map<string, (typeof cells)[0]>();
    let min = 1, max = 0, total = 0, count = 0;

    cells.forEach((cell) => {
      xSet.add(cell.x_bin);
      ySet.add(cell.y_bin);
      map.set(`${cell.x_bin}|${cell.y_bin}`, cell);

      if (cell.synth_count > 0) {
        min = Math.min(min, cell.metric_value);
        max = Math.max(max, cell.metric_value);
        total += cell.metric_value * cell.synth_count;
        count += cell.synth_count;
      }
    });

    // Sort by numeric value
    const sortByBin = (a: string, b: string) => parseBinBounds(a)[0] - parseBinBounds(b)[0];

    return {
      xLabels: [...xSet].sort(sortByBin),
      yLabels: [...ySet].sort(sortByBin).reverse(), // High values at top
      cellMap: map,
      stats: {
        min: count > 0 ? min : 0,
        max: count > 0 ? max : 0,
        avg: count > 0 ? total / count : 0,
        totalSynths: count,
      },
    };
  }, [cells]);

  const xLabel = getLabel(x_axis);
  const yLabel = getLabel(y_axis);

  return (
    <div className="space-y-3">
      {/* Header with summary stats */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-4 text-slate-500">
          <span>
            Taxa de falha: <strong className="text-slate-700">{(stats.min * 100).toFixed(0)}%</strong> a{' '}
            <strong className="text-slate-700">{(stats.max * 100).toFixed(0)}%</strong>
          </span>
          <span className="text-slate-300">|</span>
          <span>
            Média: <strong className="text-slate-700">{(stats.avg * 100).toFixed(1)}%</strong>
          </span>
        </div>
        <span className="text-slate-400">{stats.totalSynths} synths</span>
      </div>

      {/* Main visualization */}
      <div className="relative">
        {/* Y-axis label (rotated) */}
        <div
          className="absolute -left-1 top-1/2 -translate-y-1/2 -translate-x-full"
          style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg) translateX(100%)' }}
        >
          <span className="text-[11px] font-medium text-slate-600 tracking-wide">
            {yLabel.short} →
          </span>
        </div>

        {/* Grid container */}
        <div className="ml-8">
          {/* Y-axis tick labels */}
          <div className="flex">
            <div className="w-12 flex flex-col justify-between pr-2 py-1">
              {yLabels.map((bin, i) => (
                <div
                  key={bin}
                  className="text-[10px] text-slate-400 text-right leading-none"
                  style={{ height: i === 0 || i === yLabels.length - 1 ? 'auto' : 0, visibility: i === 0 || i === yLabels.length - 1 ? 'visible' : 'hidden' }}
                >
                  {i === yLabels.length - 1 ? '0%' : i === 0 ? '100%' : ''}
                </div>
              ))}
            </div>

            {/* Heatmap grid */}
            <div className="flex-1">
              <div
                className="inline-grid gap-px bg-slate-200 rounded-lg overflow-hidden shadow-sm mx-auto"
                style={{
                  gridTemplateColumns: `repeat(${xLabels.length}, 64px)`,
                  gridTemplateRows: `repeat(${yLabels.length}, 64px)`,
                }}
              >
                {yLabels.map((yBin) =>
                  xLabels.map((xBin) => {
                    const cell = cellMap.get(`${xBin}|${yBin}`);
                    const value = cell?.metric_value ?? 0;
                    const count = cell?.synth_count ?? 0;
                    const isEmpty = count === 0;

                    const bgColor = isEmpty
                      ? 'rgb(248, 250, 252)'
                      : getHeatmapColor(value, stats.min, stats.max);
                    const textColor = isEmpty
                      ? 'rgb(148, 163, 184)'
                      : getTextColor(value, stats.min, stats.max);

                    return (
                      <div
                        key={`${xBin}|${yBin}`}
                        className="w-16 h-16 flex items-center justify-center"
                        style={{ backgroundColor: bgColor }}
                        title={`${xLabel.full}: ${formatBinLabel(xBin)}\n${yLabel.full}: ${formatBinLabel(yBin)}\nTaxa de falha: ${(value * 100).toFixed(1)}%\nSynths: ${count}`}
                      >
                        <div className="text-center" style={{ color: textColor }}>
                          <div className="text-sm font-semibold leading-none">
                            {isEmpty ? '–' : `${(value * 100).toFixed(0)}%`}
                          </div>
                          {!isEmpty && count > 0 && (
                            <div className="text-[10px] opacity-70 mt-0.5">
                              n={count}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* X-axis tick labels */}
              <div className="flex justify-between mt-1.5 px-1">
                <span className="text-[10px] text-slate-400">0%</span>
                <span className="text-[10px] text-slate-400">100%</span>
              </div>
            </div>
          </div>

          {/* X-axis label */}
          <div className="text-center mt-2">
            <span className="text-[11px] font-medium text-slate-600 tracking-wide">
              {xLabel.short} →
            </span>
          </div>
        </div>
      </div>

      {/* Color legend */}
      <div className="flex items-center justify-center gap-3 pt-2">
        <span className="text-[10px] text-slate-500">Menor falha</span>
        <div
          className="h-2 w-32 rounded-full shadow-inner"
          style={{
            background: `linear-gradient(to right,
              hsl(210, 70%, 45%),
              hsl(195, 20%, 70%),
              hsl(30, 60%, 60%),
              hsl(5, 85%, 45%)
            )`,
          }}
        />
        <span className="text-[10px] text-slate-500">Maior falha</span>
      </div>
    </div>
  );
}
