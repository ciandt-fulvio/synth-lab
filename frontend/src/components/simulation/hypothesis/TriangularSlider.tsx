/**
 * TriangularSlider component.
 *
 * Ultra-dense single-line slider for triangular distribution.
 * Design: Compact table row - minimal vertical space.
 *
 * Layout (single line):
 * │ variable_name: Description...  Mín [0] ══●══ [100] Máx  Provável [40] │
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';

export interface TriangularParams {
  min: number;
  mode: number;
  max: number;
}

interface TriangularSliderProps {
  variableName: string;
  variableLabel: string;
  variableDescription?: string | null;
  initialParams: TriangularParams;
  onChange: (params: TriangularParams) => void;
  unit?: string | null;
  disabled?: boolean;
}

export function TriangularSlider({
  variableName,
  variableLabel,
  variableDescription,
  initialParams,
  onChange,
  unit,
  disabled = false,
}: TriangularSliderProps) {
  const [params, setParams] = useState<TriangularParams>(initialParams);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    setParams(initialParams);
  }, [initialParams]);

  const step = useMemo(() => {
    const range = params.max - params.min;
    if (range === 0) return 1;
    if (range >= 100) return 10;
    if (range >= 10) return 1;
    return range / 10;
  }, [params.min, params.max]);

  const modePosition = useMemo(() => {
    const range = params.max - params.min;
    if (range === 0) return 50;
    return ((params.mode - params.min) / range) * 100;
  }, [params]);

  const roundToStep = useCallback((value: number) => {
    return Math.round(value / step) * step;
  }, [step]);

  const formatDisplay = useCallback((value: number) => {
    if (step >= 1) return Math.round(value);
    return Math.round(value * 100) / 100;
  }, [step]);

  const handleModeChange = useCallback(
    (newMode: number) => {
      const rounded = roundToStep(newMode);
      const clampedMode = Math.max(params.min, Math.min(params.max, rounded));
      const newParams = { ...params, mode: clampedMode };
      setParams(newParams);
      onChange(newParams);
    },
    [params, onChange, roundToStep]
  );

  const handleInputChange = useCallback(
    (field: keyof TriangularParams, value: string) => {
      const numValue = parseFloat(value);
      if (isNaN(numValue)) return;

      const newParams = { ...params, [field]: numValue };

      if (field === 'min' && numValue > params.mode) {
        newParams.mode = numValue;
      }
      if (field === 'max' && numValue < params.mode) {
        newParams.mode = numValue;
      }
      if (field === 'mode') {
        newParams.mode = Math.max(params.min, Math.min(params.max, numValue));
      }

      setParams(newParams);
      onChange(newParams);
    },
    [params, onChange]
  );

  const handleTrackClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (disabled) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const percentage = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
      const newMode = params.min + (percentage / 100) * (params.max - params.min);
      handleModeChange(newMode);
    },
    [disabled, params, handleModeChange]
  );

  const handleThumbMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (disabled) return;
      e.preventDefault();
      setIsDragging(true);

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const track = document.getElementById(`track-${variableName}`);
        if (!track) return;
        const rect = track.getBoundingClientRect();
        const percentage = Math.max(0, Math.min(100, ((moveEvent.clientX - rect.left) / rect.width) * 100));
        const newMode = params.min + (percentage / 100) * (params.max - params.min);
        handleModeChange(newMode);
      };

      const handleMouseUp = () => {
        setIsDragging(false);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [disabled, variableName, params, handleModeChange]
  );

  return (
    <div className={cn(
      "group flex items-center gap-3 py-2 px-3 border-b border-slate-100 last:border-b-0",
      "hover:bg-slate-50/50 transition-colors"
    )}>
      {/* Label + Description (fixed width) */}
      <div className="w-64 flex-shrink-0 min-w-0">
        <div className="flex items-baseline gap-1 truncate">
          <span className="text-sm font-medium text-slate-700">{variableLabel}</span>
          {variableDescription && (
            <>
              <span className="text-slate-300">:</span>
              <span className="text-xs text-slate-400 truncate" title={variableDescription}>
                {variableDescription}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Controls row */}
      <div className="flex items-center gap-2 flex-1">
        {/* Min */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <span className="text-[10px] text-slate-400 uppercase">Mín</span>
          <Input
            type="number"
            value={formatDisplay(params.min)}
            onChange={(e) => handleInputChange('min', e.target.value)}
            disabled={disabled}
            className={cn(
              "w-14 h-6 text-center text-xs font-mono px-1",
              "border-slate-200 bg-white rounded",
              "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            )}
          />
        </div>

        {/* Slider */}
        <div
          id={`track-${variableName}`}
          onClick={handleTrackClick}
          className="relative flex-1 h-1 rounded-full cursor-pointer bg-slate-200 min-w-[100px]"
        >
          <div
            className="absolute top-0 left-0 h-full rounded-full bg-amber-400"
            style={{ width: `${modePosition}%` }}
          />
          <div
            onMouseDown={handleThumbMouseDown}
            className={cn(
              "absolute top-1/2 -translate-y-1/2 -translate-x-1/2",
              "w-3 h-3 rounded-full bg-white border-2 border-amber-500 shadow-sm cursor-grab",
              isDragging && "scale-125 cursor-grabbing",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            style={{ left: `${modePosition}%` }}
          />
        </div>

        {/* Max */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <Input
            type="number"
            value={formatDisplay(params.max)}
            onChange={(e) => handleInputChange('max', e.target.value)}
            disabled={disabled}
            className={cn(
              "w-14 h-6 text-center text-xs font-mono px-1",
              "border-slate-200 bg-white rounded",
              "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            )}
          />
          <span className="text-[10px] text-slate-400 uppercase">Máx</span>
        </div>

        {/* Mode */}
        <div className="flex items-center gap-1 flex-shrink-0 ml-2 px-2 py-0.5 rounded bg-amber-50 border border-amber-100">
          <span className="text-[10px] text-amber-600 font-medium">Provável</span>
          <Input
            type="number"
            value={formatDisplay(params.mode)}
            onChange={(e) => handleInputChange('mode', e.target.value)}
            disabled={disabled}
            className={cn(
              "w-12 h-5 text-center text-xs font-mono font-semibold px-0",
              "border-0 bg-transparent text-amber-700",
              "focus:ring-0 focus:outline-none",
              "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            )}
          />
          {unit && <span className="text-[10px] text-amber-500">{unit}</span>}
        </div>
      </div>
    </div>
  );
}
