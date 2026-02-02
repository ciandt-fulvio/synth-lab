/**
 * HypothesisReviewStep component for the wizard review step.
 *
 * Displays generated hypotheses with uncertainty indicators for variables
 * that have high uncertainty scores (those that were not clarified).
 *
 * References:
 * - Spec: specs/036-simplified-hypothesis-wizard/spec.md (US3)
 * - Types: types/hypothesis.ts
 */

import { AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { getDistributionLabel } from '../DistributionPicker';
import type { Hypothesis, DistributionParameters } from '@/types/hypothesis';

interface HypothesisReviewStepProps {
  /** Generated hypotheses to review. */
  hypotheses: Hypothesis[];
  /** Variable names with high uncertainty (not clarified). */
  highUncertaintyVars?: string[];
}

/**
 * Format a distribution parameter for display.
 */
function formatParam(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(3);
}

/**
 * Get distribution summary text.
 */
function getDistributionSummary(params: DistributionParameters): string {
  const type = params.distribution_type;
  switch (type) {
    case 'normal':
      return `μ=${formatParam(params.mean)}, σ=${formatParam(params.std_dev)}`;
    case 'uniform':
      return `[${formatParam(params.min_value)}, ${formatParam(params.max_value)}]`;
    case 'beta':
      return `α=${formatParam(params.alpha)}, β=${formatParam(params.beta)}`;
    case 'lognormal':
      return `μ=${formatParam(params.mean)}, σ=${formatParam(params.std_dev)}`;
    case 'bernoulli':
      return `p=${formatParam(params.mean)}`;
    case 'triangular':
      return `min=${formatParam(params.min_value)}, mode=${formatParam(params.mode)}, max=${formatParam(params.max_value)}`;
    default:
      return '-';
  }
}

/**
 * HypothesisReviewStep displays hypotheses with uncertainty indicators.
 */
export function HypothesisReviewStep({
  hypotheses,
  highUncertaintyVars = [],
}: HypothesisReviewStepProps) {
  const highUncertaintySet = new Set(highUncertaintyVars);

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-section-title">
          Hipóteses Geradas ({hypotheses.length})
        </h3>
        <p className="text-sm text-slate-600 mt-1">
          Revise as distribuições de probabilidade geradas para cada variável.
          {highUncertaintyVars.length > 0 && (
            <span className="text-amber-600 ml-1">
              {highUncertaintyVars.length} variáveis com alta incerteza.
            </span>
          )}
        </p>
      </div>

      <div className="divide-y divide-slate-100">
        {hypotheses.map((hyp) => {
          const isHighUncertainty = highUncertaintySet.has(hyp.variable_name);

          return (
            <div
              key={hyp.id}
              className={`flex items-center gap-4 py-3 px-2 rounded ${
                isHighUncertainty ? 'bg-amber-50/50' : ''
              }`}
            >
              {/* Status icon */}
              <div className="flex-shrink-0">
                {isHighUncertainty ? (
                  <Tooltip>
                    <TooltipTrigger>
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Alta incerteza - considere responder as perguntas de clarificação</p>
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
              </div>

              {/* Variable name */}
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium text-slate-900 truncate block">
                  {hyp.variable_name}
                </span>
              </div>

              {/* Distribution type */}
              <div className="flex-shrink-0">
                <span className="badge-neutral text-xs">
                  {getDistributionLabel(hyp.parameters.distribution_type)}
                </span>
              </div>

              {/* Parameters */}
              <div className="flex-shrink-0 text-right">
                <span className="text-xs text-slate-500 font-mono">
                  {getDistributionSummary(hyp.parameters)}
                </span>
              </div>

              {/* Scenario indicator */}
              {hyp.selected_scenario && (
                <div className="flex-shrink-0">
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3.5 w-3.5 text-slate-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Cenário: {hyp.selected_scenario}</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
