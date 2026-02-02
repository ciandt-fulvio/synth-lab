/**
 * ScenarioProfileSelector component.
 *
 * Radio button group for selecting hypothesis generation scenario profile:
 * - Conservative: Worse-than-average outcomes, higher uncertainty
 * - Realistic: Market-average parameters (default)
 * - Optimistic: Better-than-average outcomes, lower uncertainty
 *
 * Design: Clean, scientific, data-focused with clear visual distinction.
 *
 * References:
 * - Spec: specs/036-simplified-hypothesis-wizard/spec.md
 * - Research: specs/036-simplified-hypothesis-wizard/research.md
 */

import { cn } from '@/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { TrendingDown, Minus, TrendingUp } from 'lucide-react';

export type ScenarioProfile = 'conservative' | 'realistic' | 'optimistic';

interface ScenarioProfileOption {
  value: ScenarioProfile;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  colorClass: string;
  bgClass: string;
  borderClass: string;
}

const PROFILE_OPTIONS: ScenarioProfileOption[] = [
  {
    value: 'conservative',
    label: 'Conservador',
    description: 'Resultados piores que a média, maior incerteza',
    icon: TrendingDown,
    colorClass: 'text-red-700',
    bgClass: 'bg-red-50',
    borderClass: 'border-red-300',
  },
  {
    value: 'realistic',
    label: 'Realista',
    description: 'Parâmetros médios de mercado (padrão)',
    icon: Minus,
    colorClass: 'text-slate-700',
    bgClass: 'bg-slate-50',
    borderClass: 'border-slate-300',
  },
  {
    value: 'optimistic',
    label: 'Otimista',
    description: 'Resultados melhores que a média, menor incerteza',
    icon: TrendingUp,
    colorClass: 'text-green-700',
    bgClass: 'bg-green-50',
    borderClass: 'border-green-300',
  },
];

interface ScenarioProfileSelectorProps {
  value: ScenarioProfile;
  onChange: (value: ScenarioProfile) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Scenario profile selector with visual distinction for each option.
 */
export function ScenarioProfileSelector({
  value,
  onChange,
  disabled = false,
  className,
}: ScenarioProfileSelectorProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <div className="space-y-1">
        <h3 className="text-section-title">Perfil de Cenário</h3>
        <p className="text-sm text-slate-600">
          Escolha como gerar as distribuições de probabilidade para as variáveis
        </p>
      </div>

      <RadioGroup
        value={value}
        onValueChange={(v) => onChange(v as ScenarioProfile)}
        disabled={disabled}
        className="grid gap-3"
      >
        {PROFILE_OPTIONS.map((option) => {
          const isSelected = value === option.value;
          const Icon = option.icon;

          return (
            <Label
              key={option.value}
              htmlFor={`profile-${option.value}`}
              className={cn(
                'relative flex items-start gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all',
                'hover:shadow-sm',
                isSelected
                  ? cn(
                      option.borderClass,
                      option.bgClass,
                      'shadow-sm'
                    )
                  : 'border-slate-200 bg-white hover:border-slate-300',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              {/* Radio button indicator */}
              <div className="flex-shrink-0 pt-0.5">
                <span
                  className={cn(
                    'relative w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all',
                    isSelected
                      ? cn(option.borderClass, 'bg-white')
                      : 'border-slate-300 bg-white'
                  )}
                >
                  {isSelected && (
                    <span
                      className={cn(
                        'w-2.5 h-2.5 rounded-full',
                        option.value === 'conservative' && 'bg-red-600',
                        option.value === 'realistic' && 'bg-slate-600',
                        option.value === 'optimistic' && 'bg-green-600'
                      )}
                    />
                  )}
                </span>
                <RadioGroupItem
                  value={option.value}
                  id={`profile-${option.value}`}
                  className="sr-only"
                />
              </div>

              {/* Icon */}
              <div
                className={cn(
                  'flex-shrink-0 mt-0.5',
                  isSelected ? option.colorClass : 'text-slate-400'
                )}
              >
                <Icon className="h-5 w-5" />
              </div>

              {/* Content */}
              <div className="flex-1 space-y-1">
                <div
                  className={cn(
                    'font-semibold text-[15px]',
                    isSelected ? option.colorClass : 'text-slate-800'
                  )}
                >
                  {option.label}
                </div>
                <p
                  className={cn(
                    'text-sm',
                    isSelected ? option.colorClass : 'text-slate-600'
                  )}
                >
                  {option.description}
                </p>
              </div>
            </Label>
          );
        })}
      </RadioGroup>

      {/* Help text */}
      <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <p className="text-xs text-slate-600 leading-relaxed">
          <span className="font-medium">Dica:</span> O perfil ajusta automaticamente as
          distribuições de todas as variáveis. Escolha{' '}
          <span className="font-medium text-slate-700">Conservador</span> para análise de
          risco,{' '}
          <span className="font-medium text-slate-700">Realista</span> para projeções
          padrão, ou{' '}
          <span className="font-medium text-slate-700">Otimista</span> para cenários de
          melhor caso.
        </p>
      </div>
    </div>
  );
}
