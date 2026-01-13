/**
 * DistributionSlider component for synth group creation.
 *
 * A linked slider group that maintains a total sum of 1.0 (100%).
 * When one slider is adjusted, others are proportionally adjusted.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md
 *   - Types: src/types/synthGroup.ts
 */

import { useCallback, useMemo } from 'react';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SliderItem {
  key: string;
  label: string;
  value: number;
}

interface DistributionSliderProps {
  /** Label for the distribution group */
  label: string;
  /** Description text */
  description?: string;
  /** Items in the distribution */
  items: SliderItem[];
  /** Callback when values change */
  onChange: (items: SliderItem[]) => void;
  /** Whether the slider is disabled */
  disabled?: boolean;
  /** Color theme for the sliders */
  colorScheme?: 'indigo' | 'emerald' | 'amber' | 'rose' | 'slate';
  /** Optional reset callback */
  onReset?: () => void;
}

const COLOR_SCHEMES = {
  indigo: {
    track: 'bg-indigo-100',
    range: 'bg-gradient-to-r from-indigo-500 to-violet-500',
    thumb: 'border-indigo-500 hover:border-indigo-600',
    label: 'text-indigo-700',
    badge: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  },
  emerald: {
    track: 'bg-emerald-100',
    range: 'bg-gradient-to-r from-emerald-500 to-teal-500',
    thumb: 'border-emerald-500 hover:border-emerald-600',
    label: 'text-emerald-700',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  amber: {
    track: 'bg-amber-100',
    range: 'bg-gradient-to-r from-amber-500 to-orange-500',
    thumb: 'border-amber-500 hover:border-amber-600',
    label: 'text-amber-700',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  rose: {
    track: 'bg-rose-100',
    range: 'bg-gradient-to-r from-rose-500 to-pink-500',
    thumb: 'border-rose-500 hover:border-rose-600',
    label: 'text-rose-700',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
  },
  slate: {
    track: 'bg-slate-200',
    range: 'bg-gradient-to-r from-slate-500 to-slate-600',
    thumb: 'border-slate-500 hover:border-slate-600',
    label: 'text-slate-700',
    badge: 'bg-slate-100 text-slate-700 border-slate-300',
  },
};

// Mesmas cores do DistributionDisplay para consistência visual
const DISTRIBUTION_COLORS = [
  { bg: 'bg-blue-500', hex: '#3b82f6' },      // Azul
  { bg: 'bg-violet-500', hex: '#8b5cf6' },    // Violeta
  { bg: 'bg-fuchsia-500', hex: '#d946ef' },   // Fúcsia/Rosa
  { bg: 'bg-amber-500', hex: '#f59e0b' },     // Laranja/Âmbar
  { bg: 'bg-teal-500', hex: '#14b8a6' },      // Verde-azulado
];

export function DistributionSlider({
  label,
  description,
  items,
  onChange,
  disabled = false,
  colorScheme = 'indigo',
  onReset,
}: DistributionSliderProps) {
  const colors = COLOR_SCHEMES[colorScheme];

  // Calculate total - should always be 1.0
  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.value, 0),
    [items]
  );

  const isValid = Math.abs(total - 1.0) < 0.01;

  // Handle slider change with redistribution
  const handleSliderChange = useCallback(
    (changedKey: string, newValue: number) => {
      const oldItem = items.find((item) => item.key === changedKey);
      if (!oldItem) return;

      const oldValue = oldItem.value;
      const delta = newValue - oldValue;

      // If no change, return
      if (Math.abs(delta) < 0.001) return;

      // Get other items that can absorb the change
      const otherItems = items.filter((item) => item.key !== changedKey);
      const otherTotal = otherItems.reduce((sum, item) => sum + item.value, 0);

      // If trying to take more than available, cap it
      const maxNewValue = Math.min(newValue, 1.0);
      const actualDelta = maxNewValue - oldValue;

      // Redistribute among other items proportionally
      const newItems = items.map((item) => {
        if (item.key === changedKey) {
          return { ...item, value: maxNewValue };
        }

        // Calculate this item's share of the redistribution
        if (otherTotal > 0.001) {
          const proportion = item.value / otherTotal;
          const adjustment = actualDelta * proportion;
          const newVal = Math.max(0, item.value - adjustment);
          return { ...item, value: newVal };
        }

        return item;
      });

      // Normalize to ensure sum is exactly 1.0
      const newTotal = newItems.reduce((sum, item) => sum + item.value, 0);
      if (newTotal > 0.001) {
        const normalizedItems = newItems.map((item) => ({
          ...item,
          value: item.value / newTotal,
        }));
        onChange(normalizedItems);
      }
    },
    [items, onChange]
  );

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1">
          <h4 className="text-sm font-semibold text-indigo-700">{label}</h4>
          {onReset && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onReset}
              className="h-6 px-2 text-xs text-slate-500 hover:text-indigo-600"
              title="Resetar para padrão IBGE"
            >
              <RotateCcw className="h-3 w-3" />
            </Button>
          )}
        </div>
        <div
          className={cn(
            'px-2 py-0.5 rounded-md text-xs font-medium border transition-colors bg-indigo-50 text-indigo-700 border-indigo-200'
          )}
        >
          {(total * 100).toFixed(0)}%
        </div>
      </div>

      {/* Sliders */}
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.key} className="group">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-slate-600 group-hover:text-slate-900 transition-colors">
                {item.label}
              </label>
              <span
                className={cn(
                  'text-xs font-mono tabular-nums px-1.5 py-0.5 rounded transition-all',
                  'bg-slate-50 text-slate-600 group-hover:bg-slate-100'
                )}
              >
                {(item.value * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              min={0}
              max={1}
              step={0.01}
              value={[item.value]}
              onValueChange={(value) => handleSliderChange(item.key, value[0])}
              disabled={disabled}
              className={cn(
                'transition-opacity',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            />
          </div>
        ))}
      </div>

      {/* Visual Distribution Bar */}
      <div className="space-y-2">
        <div className="h-2 w-full rounded-full overflow-hidden flex bg-slate-100 mt-6">
          {items.map((item, index) => {
            const colorData = DISTRIBUTION_COLORS[index % DISTRIBUTION_COLORS.length];
            return (
              <div
                key={item.key}
                className="h-full transition-all duration-300 ease-out first:rounded-l-full last:rounded-r-full"
                style={{
                  width: `${item.value * 100}%`,
                  backgroundColor: colorData.hex,
                }}
                title={`${item.label}: ${(item.value * 100).toFixed(0)}%`}
              />
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 justify-center">
          {items.map((item, index) => {
            const colorData = DISTRIBUTION_COLORS[index % DISTRIBUTION_COLORS.length];
            return (
              <div key={item.key} className="flex items-center gap-1.5">
                <div
                  className="w-2.5 h-2.5 rounded-sm"
                  style={{ backgroundColor: colorData.hex }}
                />
                <span className="text-xs text-slate-600">
                  {item.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
