/**
 * StepIndicator component for simulation wizard.
 *
 * Shows progress through the simulation creation flow with clickable completed steps.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  id: string;
  label: string;
  status: 'pending' | 'current' | 'completed' | 'processing';
}

interface StepIndicatorProps {
  steps: Step[];
  className?: string;
  /** Currently viewed step (for reviewing completed steps) */
  viewedStep?: string | null;
  /** Callback when a completed step is clicked */
  onStepClick?: (stepId: string) => void;
}

/**
 * Step indicator showing progress through simulation wizard.
 * Completed steps are clickable for reviewing previous steps.
 */
export function StepIndicator({ steps, className, viewedStep, onStepClick }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className={cn('w-full', className)}>
      <ol className="flex items-center">
        {steps.map((step, stepIdx) => {
          // Completed and current steps are clickable
          const isClickable = (step.status === 'completed' || step.status === 'current') && onStepClick;
          const isViewed = viewedStep === step.id;

          return (
            <li
              key={step.id}
              className="flex-1 flex flex-col items-center relative"
            >
              {/* Connector line - before */}
              {stepIdx > 0 && (
                <div
                  className={cn(
                    'absolute top-4 right-1/2 w-full h-0.5 -translate-y-1/2 transition-colors',
                    steps[stepIdx - 1].status === 'completed' ? 'bg-indigo-600' : 'bg-slate-200'
                  )}
                />
              )}

              {/* Step circle */}
              <button
                type="button"
                onClick={() => isClickable && onStepClick(step.id)}
                disabled={!isClickable}
                className={cn(
                  'relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all duration-200',
                  // Completed state
                  step.status === 'completed' && !isViewed &&
                    'border-indigo-600 bg-indigo-600 text-white',
                  // Completed + viewed state
                  step.status === 'completed' && isViewed &&
                    'border-indigo-600 bg-white text-indigo-600 ring-2 ring-indigo-600 ring-offset-2',
                  // Current state
                  step.status === 'current' &&
                    'border-indigo-600 bg-white text-indigo-600',
                  // Processing state
                  step.status === 'processing' &&
                    'border-indigo-600 bg-indigo-50 text-indigo-600',
                  // Pending state
                  step.status === 'pending' &&
                    'border-slate-300 bg-white text-slate-400',
                  // Clickable hover effect
                  isClickable && 'cursor-pointer hover:scale-110 hover:shadow-md'
                )}
                aria-label={isClickable ? `Ir para ${step.label}` : undefined}
              >
                {step.status === 'completed' ? (
                  <Check className="h-4 w-4" />
                ) : step.status === 'processing' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span className="text-sm font-medium">{stepIdx + 1}</span>
                )}
              </button>

              {/* Label */}
              <span
                className={cn(
                  'mt-2 text-xs font-medium text-center transition-colors',
                  step.status === 'completed' && 'text-indigo-600',
                  step.status === 'current' && 'text-indigo-600',
                  step.status === 'processing' && 'text-indigo-600',
                  step.status === 'pending' && 'text-slate-500',
                  isViewed && 'font-semibold'
                )}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/**
 * Helper to compute step statuses from simulation status.
 */
export function getWizardSteps(simulationStatus: string): Step[] {
  const statusMap: Record<string, number> = {
    parsing: 0,
    awaiting_question_validation: 0,
    dag_construction: 1,
    awaiting_dag_validation: 1,
    hypothesis_generation: 2,
    awaiting_hypothesis_validation: 2,
    ready_to_run: 2,
    simulating: 2,
    completed: 3,
    failed: -1,
  };

  const processingStatuses = ['parsing', 'dag_construction', 'hypothesis_generation', 'simulating'];
  const currentStepIndex = statusMap[simulationStatus] ?? 0;
  const isProcessing = processingStatuses.includes(simulationStatus);

  const steps: Step[] = [
    { id: 'question', label: 'Pergunta & Cenário', status: 'pending' },
    { id: 'dag', label: 'Modelo Causal', status: 'pending' },
    { id: 'refinement', label: 'Refinamento', status: 'pending' },
    { id: 'results', label: 'Resultados', status: 'pending' },
  ];

  return steps.map((step, idx) => {
    if (idx < currentStepIndex) {
      return { ...step, status: 'completed' as const };
    } else if (idx === currentStepIndex) {
      return { ...step, status: isProcessing ? 'processing' as const : 'current' as const };
    }
    return step;
  });
}

export type { Step };
