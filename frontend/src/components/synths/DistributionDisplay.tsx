/**
 * T030 DistributionDisplay component.
 *
 * Read-only visualization of a distribution as a horizontal bar chart.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md (US3)
 *   - Types: src/types/synthGroup.ts
 */

import { cn } from '@/lib/utils';

interface DistributionItem {
  label: string;
  value: number;
  color?: string;
}

interface DistributionDisplayProps {
  title: string;
  items: DistributionItem[];
  className?: string;
}

const DEFAULT_COLORS = [
  'bg-blue-500',      // Azul
  'bg-violet-500',    // Violeta
  'bg-fuchsia-500',   // Fúcsia/Rosa
  'bg-amber-500',     // Laranja/Âmbar
  'bg-teal-500',      // Verde-azulado
];

export function DistributionDisplay({ title, items, className }: DistributionDisplayProps) {
  // Calculate total for normalization (should be ~1.0, but might vary slightly)
  const total = items.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className={cn('space-y-2', className)}>
      <h4 className="text-sm font-medium text-slate-700">{title}</h4>

      {/* Distribution bar */}
      <div className="h-3 rounded-full bg-slate-100 overflow-hidden flex">
        {items.map((item, index) => {
          const percentage = total > 0 ? (item.value / total) * 100 : 0;
          if (percentage < 0.5) return null; // Don't render very small segments
          return (
            <div
              key={item.label}
              className={cn(
                item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
                'transition-all duration-300'
              )}
              style={{ width: `${percentage}%` }}
              title={`${item.label}: ${(item.value * 100).toFixed(1)}%`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {items.map((item, index) => (
          <div key={item.label} className="flex items-center gap-1.5 text-xs">
            <div
              className={cn(
                'w-2.5 h-2.5 rounded-sm',
                item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]
              )}
            />
            <span className="text-slate-600">{item.label}</span>
            <span className="text-slate-400">({(item.value * 100).toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
