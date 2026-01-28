/**
 * ScenarioSelector component.
 *
 * Compact inline radio button group for selecting pre-defined scenarios.
 * Design: Scientific/editorial - clean, precise, data-focused.
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  Variable Label                                             │
 * │  ( ) Option A    (●) Option B    ( ) Option C               │
 * └─────────────────────────────────────────────────────────────┘
 */

import { cn } from '@/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import type { ScenarioOption } from '@/types/hypothesis';

interface ScenarioSelectorProps {
  variableName: string;
  variableLabel: string;
  variableDescription?: string | null;
  options: ScenarioOption[];
  selectedValue?: string | null;
  onChange: (value: string) => void;
  disabled?: boolean;
}

/**
 * Compact inline radio button selector for scenario choices.
 */
export function ScenarioSelector({
  variableName,
  variableLabel,
  variableDescription,
  options,
  selectedValue,
  onChange,
  disabled = false,
}: ScenarioSelectorProps) {
  if (!options || options.length === 0) {
    return (
      <div className="text-sm text-slate-400 italic py-3 px-4 bg-slate-50/50 rounded border border-dashed border-slate-200">
        Nenhuma opção de cenário disponível
      </div>
    );
  }

  return (
    <div className="group py-4 px-5 rounded-lg bg-white border border-slate-200/80 hover:border-slate-300 transition-colors">
      {/* Variable label and description */}
      <div className="mb-3">
        <div className="text-[15px] leading-snug">
          <span className="font-semibold text-slate-800">{variableLabel}</span>
          {variableDescription && (
            <>
              <span className="text-slate-600">: </span>
              <span className="text-slate-600">{variableDescription}</span>
            </>
          )}
        </div>
      </div>

      {/* Radio options in a row */}
      <RadioGroup
        value={selectedValue || ''}
        onValueChange={onChange}
        disabled={disabled}
        className="flex flex-wrap items-center gap-x-6 gap-y-2"
      >
        {options.map((option) => {
          const isSelected = selectedValue === option.value;

          return (
            <Label
              key={option.value}
              htmlFor={`${variableName}-${option.value}`}
              className={cn(
                'flex items-center gap-2 cursor-pointer transition-all select-none',
                'text-sm',
                isSelected ? 'text-amber-700' : 'text-slate-600 hover:text-slate-800',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <span
                className={cn(
                  'relative w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all',
                  isSelected
                    ? 'border-amber-500 bg-amber-500'
                    : 'border-slate-300 bg-white group-hover:border-slate-400'
                )}
              >
                {isSelected && (
                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </span>
              <RadioGroupItem
                value={option.value}
                id={`${variableName}-${option.value}`}
                className="sr-only"
              />
              <span className={cn(isSelected && 'font-medium')}>
                {option.label}
              </span>
            </Label>
          );
        })}
      </RadioGroup>
    </div>
  );
}
