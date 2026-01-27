/**
 * StepIndicator component for simulation wizard.
 *
 * Shows progress through the simulation creation flow.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { Check, Circle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  id: string;
  label: string;
  status: 'pending' | 'current' | 'completed' | 'processing';
}

interface StepIndicatorProps {
  steps: Step[];
  className?: string;
}

/**
 * Step indicator showing progress through simulation wizard.
 */
export function StepIndicator({ steps, className }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className={cn('w-full', className)}>
      <ol className="flex items-center justify-between">
        {steps.map((step, stepIdx) => (
          <li
            key={step.id}
            className={cn(
              'relative flex-1',
              stepIdx !== steps.length - 1 ? 'pr-4' : ''
            )}
          >
            <div className="flex items-center">
              {/* Step circle */}
              <div
                className={cn(
                  'relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                  step.status === 'completed' &&
                    'border-indigo-600 bg-indigo-600 text-white',
                  step.status === 'current' &&
                    'border-indigo-600 bg-white text-indigo-600',
                  step.status === 'processing' &&
                    'border-indigo-600 bg-indigo-50 text-indigo-600',
                  step.status === 'pending' &&
                    'border-slate-300 bg-white text-slate-400'
                )}
              >
                {step.status === 'completed' ? (
                  <Check className="h-4 w-4" />
                ) : step.status === 'processing' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span className="text-sm font-medium">{stepIdx + 1}</span>
                )}
              </div>

              {/* Connector line */}
              {stepIdx !== steps.length - 1 && (
                <div
                  className={cn(
                    'ml-2 flex-1 h-0.5 transition-colors',
                    step.status === 'completed' ? 'bg-indigo-600' : 'bg-slate-200'
                  )}
                />
              )}
            </div>

            {/* Label */}
            <div className="mt-2">
              <span
                className={cn(
                  'text-xs font-medium',
                  step.status === 'completed' && 'text-indigo-600',
                  step.status === 'current' && 'text-indigo-600',
                  step.status === 'processing' && 'text-indigo-600',
                  step.status === 'pending' && 'text-slate-500'
                )}
              >
                {step.label}
              </span>
            </div>
          </li>
        ))}
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
    ready_to_run: 3,
    simulating: 3,
    completed: 4,
    failed: -1,
  };

  const processingStatuses = ['parsing', 'dag_construction', 'hypothesis_generation', 'simulating'];
  const currentStepIndex = statusMap[simulationStatus] ?? 0;
  const isProcessing = processingStatuses.includes(simulationStatus);

  const steps: Step[] = [
    { id: 'question', label: 'Pergunta', status: 'pending' },
    { id: 'dag', label: 'Modelo Causal', status: 'pending' },
    { id: 'hypotheses', label: 'Hipóteses', status: 'pending' },
    { id: 'run', label: 'Simulação', status: 'pending' },
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
