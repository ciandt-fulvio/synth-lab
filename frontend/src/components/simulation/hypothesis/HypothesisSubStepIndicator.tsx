/**
 * HypothesisSubStepIndicator component.
 *
 * Visual indicator for the 4 sub-steps within the hypothesis validation step.
 *
 * References:
 *   - Design: Scientific editorial style with amber accents
 */

import { cn } from '@/lib/utils';
import { Check, Settings2, AlertTriangle, Link2, FileText } from 'lucide-react';

export type HypothesisSubStep = 1 | 2 | 3 | 4;

interface SubStepConfig {
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const SUB_STEPS: Record<HypothesisSubStep, SubStepConfig> = {
  1: {
    label: 'Controles',
    description: 'Variáveis controláveis',
    icon: Settings2,
  },
  2: {
    label: 'Incertezas',
    description: 'Incertezas críticas',
    icon: AlertTriangle,
  },
  3: {
    label: 'Relações',
    description: 'Força dos relacionamentos',
    icon: Link2,
  },
  4: {
    label: 'Resumo',
    description: 'Revisão e confirmação',
    icon: FileText,
  },
};

interface HypothesisSubStepIndicatorProps {
  currentStep: HypothesisSubStep;
  completedSteps?: HypothesisSubStep[];
  onStepClick?: (step: HypothesisSubStep) => void;
}

/**
 * Sub-step indicator showing progress through the 4 hypothesis configuration steps.
 */
export function HypothesisSubStepIndicator({
  currentStep,
  completedSteps = [],
  onStepClick,
}: HypothesisSubStepIndicatorProps) {
  const steps = [1, 2, 3, 4] as const;

  return (
    <div className="w-full">
      {/* Desktop view */}
      <div className="hidden sm:flex items-center justify-between">
        {steps.map((step, index) => {
          const config = SUB_STEPS[step];
          const Icon = config.icon;
          const isActive = step === currentStep;
          const isCompleted = completedSteps.includes(step);
          const isClickable = onStepClick && (isCompleted || step <= currentStep);

          return (
            <div key={step} className="flex items-center flex-1">
              {/* Step circle */}
              <button
                type="button"
                onClick={() => isClickable && onStepClick?.(step)}
                disabled={!isClickable}
                className={cn(
                  'flex items-center gap-3 p-2 rounded-lg transition-colors',
                  isClickable && 'cursor-pointer hover:bg-slate-50',
                  !isClickable && 'cursor-default'
                )}
              >
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors',
                    isActive && 'border-amber-500 bg-amber-50 text-amber-600',
                    isCompleted && !isActive && 'border-green-500 bg-green-50 text-green-600',
                    !isActive && !isCompleted && 'border-slate-200 bg-slate-50 text-slate-400'
                  )}
                >
                  {isCompleted && !isActive ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <div className="text-left">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      isActive && 'text-amber-700',
                      isCompleted && !isActive && 'text-green-700',
                      !isActive && !isCompleted && 'text-slate-500'
                    )}
                  >
                    {config.label}
                  </p>
                  <p className="text-xs text-slate-500">{config.description}</p>
                </div>
              </button>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-2',
                    isCompleted ? 'bg-green-300' : 'bg-slate-200'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile view - compact */}
      <div className="sm:hidden">
        <div className="flex items-center justify-center gap-2 mb-3">
          {steps.map((step) => {
            const isActive = step === currentStep;
            const isCompleted = completedSteps.includes(step);

            return (
              <div
                key={step}
                className={cn(
                  'w-2 h-2 rounded-full transition-colors',
                  isActive && 'w-3 h-3 bg-amber-500',
                  isCompleted && !isActive && 'bg-green-500',
                  !isActive && !isCompleted && 'bg-slate-300'
                )}
              />
            );
          })}
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-slate-900">
            {SUB_STEPS[currentStep].label}
          </p>
          <p className="text-xs text-slate-500">{SUB_STEPS[currentStep].description}</p>
        </div>
      </div>
    </div>
  );
}
