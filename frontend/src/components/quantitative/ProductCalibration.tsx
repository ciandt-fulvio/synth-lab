/**
 * ProductCalibration component.
 *
 * Cards for each product node allowing PM to set calibration level:
 * Low (0.2) / Medium (0.5) / High (0.8).
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { CausalNodeMeta } from '@/types/quantitative-analysis';

interface ProductCalibrationProps {
  productNodes: CausalNodeMeta[];
  onCalibrationsChange: (calibrations: Record<string, string>) => void;
}

const CALIBRATION_OPTIONS = [
  { value: 'low', label: 'Baixo', numericLabel: '0.2', color: 'bg-amber-100 text-amber-700 border-amber-300' },
  { value: 'medium', label: 'Médio', numericLabel: '0.5', color: 'bg-blue-100 text-blue-700 border-blue-300' },
  { value: 'high', label: 'Alto', numericLabel: '0.8', color: 'bg-emerald-100 text-emerald-700 border-emerald-300' },
] as const;

export function ProductCalibration({ productNodes, onCalibrationsChange }: ProductCalibrationProps) {
  const [localCalibrations, setLocalCalibrations] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const node of productNodes) {
      initial[node.name] = node.product_calibration ?? 'medium';
    }
    return initial;
  });

  // Debounce save
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onChangeRef = useRef(onCalibrationsChange);
  onChangeRef.current = onCalibrationsChange;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const handleSelect = useCallback((nodeName: string, value: string) => {
    setLocalCalibrations((prev) => {
      const updated = { ...prev, [nodeName]: value };
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => onChangeRef.current(updated), 500);
      return updated;
    });
  }, []);

  const modifiedCount = productNodes.filter(
    (n) => (localCalibrations[n.name] ?? 'medium') !== 'medium'
  ).length;

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-700">
          Calibração de Produto
        </span>
        <span className="text-xs text-slate-500">
          {modifiedCount > 0
            ? `${modifiedCount}/${productNodes.length} ajustadas`
            : `${productNodes.length} características com valor padrão`}
        </span>
      </div>

      {/* Product node cards */}
      {productNodes.map((node) => {
        const currentValue = localCalibrations[node.name] ?? 'medium';
        const isModified = currentValue !== 'medium';

        return (
          <div
            key={node.name}
            className="rounded-lg border border-slate-200 bg-white p-4 space-y-3"
          >
            {/* Name + badge */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-700">{node.name}</span>
              {isModified && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-100 text-violet-700">
                  ajustado
                </span>
              )}
            </div>

            {/* Description */}
            {node.product_description && (
              <p className="text-xs text-slate-500 leading-relaxed">
                {node.product_description}
              </p>
            )}

            {/* Calibration buttons */}
            <div className="flex gap-2">
              {CALIBRATION_OPTIONS.map((opt) => {
                const isSelected = currentValue === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    className={`flex-1 px-3 py-2 rounded-md border text-sm font-medium transition-all duration-150 ${
                      isSelected
                        ? opt.color + ' border-2'
                        : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => handleSelect(node.name, opt.value)}
                  >
                    <div className="text-center">
                      <div>{opt.label}</div>
                      <div className="text-[10px] opacity-70">{opt.numericLabel}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
