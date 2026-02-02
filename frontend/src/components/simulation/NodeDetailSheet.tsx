/**
 * NodeDetailSheet - Right-side sheet for editing DAG node details.
 *
 * Displays variable name/description (read-only), relevance selector,
 * range inputs (min/max), and save button.
 *
 * References:
 *   - Spec: specs/037-unified-dag-hypotheses/spec.md
 *   - Sheet: frontend/src/components/ui/sheet.tsx
 */

import { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import type { Variable } from '@/types/causal-dag';
import type { Hypothesis, Relevance } from '@/types/hypothesis';

interface NodeDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variable: Variable | null;
  hypothesis: Hypothesis | null;
  onSave: (data: { relevance: Relevance; range_min: number | null; range_max: number | null }) => void;
  isSaving?: boolean;
}

export function NodeDetailSheet({
  open,
  onOpenChange,
  variable,
  hypothesis,
  onSave,
  isSaving = false,
}: NodeDetailSheetProps) {
  const [relevance, setRelevance] = useState<Relevance>('medium');
  const [rangeMin, setRangeMin] = useState<string>('');
  const [rangeMax, setRangeMax] = useState<string>('');
  const [rangeError, setRangeError] = useState<string | null>(null);

  // Sync state when hypothesis changes
  useEffect(() => {
    if (hypothesis) {
      setRelevance(hypothesis.relevance || 'medium');
      setRangeMin(hypothesis.range_min != null ? String(hypothesis.range_min) : '');
      setRangeMax(hypothesis.range_max != null ? String(hypothesis.range_max) : '');
      setRangeError(null);
    }
  }, [hypothesis]);

  const handleSave = () => {
    const minVal = rangeMin.trim() === '' ? null : parseFloat(rangeMin);
    const maxVal = rangeMax.trim() === '' ? null : parseFloat(rangeMax);

    // Validate range
    if (minVal !== null && maxVal !== null && minVal > maxVal) {
      setRangeError('Valor mínimo deve ser menor ou igual ao máximo');
      return;
    }

    setRangeError(null);
    onSave({ relevance, range_min: minVal, range_max: maxVal });
  };

  if (!variable) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:w-[400px]">
        <SheetHeader>
          <SheetTitle className="text-lg">{variable.label}</SheetTitle>
          {variable.description && (
            <SheetDescription className="text-sm text-slate-500">
              {variable.description}
            </SheetDescription>
          )}
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Variable info (read-only) */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="font-medium">Escopo:</span>
              <span className="capitalize">{variable.scope}-level</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="font-medium">Tipo:</span>
              <span className="capitalize">{variable.variable_type}</span>
            </div>
          </div>

          <hr className="border-slate-200" />

          {/* Relevance selector */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Relevância
            </label>
            <div className="flex gap-2">
              {(['low', 'medium', 'high'] as Relevance[]).map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setRelevance(level)}
                  className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-all ${
                    relevance === level
                      ? level === 'high'
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : level === 'medium'
                          ? 'bg-indigo-500 text-white border-indigo-500'
                          : 'bg-indigo-400 text-white border-indigo-400'
                      : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {level === 'high' ? 'Alta' : level === 'medium' ? 'Média' : 'Baixa'}
                </button>
              ))}
            </div>
          </div>

          {/* Range inputs */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Limites de Clamping
            </label>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-xs text-slate-500 mb-1">Mínimo</label>
                <input
                  type="number"
                  step="any"
                  value={rangeMin}
                  onChange={(e) => {
                    setRangeMin(e.target.value);
                    setRangeError(null);
                  }}
                  placeholder="Sem limite"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <span className="text-slate-400 pt-5">—</span>
              <div className="flex-1">
                <label className="block text-xs text-slate-500 mb-1">Máximo</label>
                <input
                  type="number"
                  step="any"
                  value={rangeMax}
                  onChange={(e) => {
                    setRangeMax(e.target.value);
                    setRangeError(null);
                  }}
                  placeholder="Sem limite"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>
            {rangeError && (
              <p className="mt-2 text-sm text-red-600">{rangeError}</p>
            )}
            <p className="mt-2 text-xs text-slate-400">
              Deixe vazio para não limitar. Amostras da distribuição serão cortadas nesses limites.
            </p>
          </div>

          {/* Save button */}
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="w-full btn-primary disabled:opacity-50"
          >
            {isSaving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
