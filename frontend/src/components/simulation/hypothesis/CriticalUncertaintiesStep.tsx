/**
 * CriticalUncertaintiesStep component (Layer B).
 *
 * Dense list of critical uncertainties with inline sliders.
 * Design: Compact table-like layout.
 */

import { useMemo } from 'react';
import { AlertTriangle, HelpCircle } from 'lucide-react';
import { TriangularSlider, TriangularParams } from './TriangularSlider';
import type { Variable } from '@/types/causal-dag';
import type { Hypothesis } from '@/types/hypothesis';

interface CriticalUncertaintiesStepProps {
  variables: Variable[];
  hypotheses: Hypothesis[];
  params: Record<string, TriangularParams>;
  onChange: (variableName: string, params: TriangularParams) => void;
  readOnly?: boolean;
}

function filterCriticalUncertainties(variables: Variable[]): Variable[] {
  return variables.filter(
    (v) => v.is_critical_uncertainty && !v.is_outcome
  );
}

function getTriangularParams(hypothesis: Hypothesis | undefined): TriangularParams {
  if (!hypothesis?.parameters) {
    return { min: 0, mode: 50, max: 100 };
  }

  const p = hypothesis.parameters;

  if (p.distribution_type === 'triangular' && p.min_value != null && p.max_value != null) {
    return {
      min: p.min_value,
      mode: p.mode ?? (p.min_value + p.max_value) / 2,
      max: p.max_value,
    };
  }

  if (p.distribution_type === 'uniform' && p.min_value != null && p.max_value != null) {
    return {
      min: p.min_value,
      mode: (p.min_value + p.max_value) / 2,
      max: p.max_value,
    };
  }

  if (p.distribution_type === 'normal' && p.mean != null) {
    const std = p.std_dev ?? 10;
    return {
      min: p.mean - 2 * std,
      mode: p.mean,
      max: p.mean + 2 * std,
    };
  }

  return { min: 0, mode: 50, max: 100 };
}

export function CriticalUncertaintiesStep({
  variables,
  hypotheses,
  params,
  onChange,
  readOnly = false,
}: CriticalUncertaintiesStepProps) {
  const criticalVars = useMemo(
    () => filterCriticalUncertainties(variables),
    [variables]
  );

  const hypothesisByVar = useMemo(() => {
    const map: Record<string, Hypothesis> = {};
    for (const h of hypotheses) {
      map[h.variable_name] = h;
    }
    return map;
  }, [hypotheses]);

  if (criticalVars.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 border border-dashed border-slate-200 rounded-lg bg-slate-50/50">
        <HelpCircle className="h-8 w-8 text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 text-center">
          Nenhuma incerteza crítica identificada
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <AlertTriangle className="h-4 w-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-700">Incertezas Críticas</span>
        <span className="text-xs text-slate-400">({criticalVars.length})</span>
      </div>

      {/* Dense list */}
      <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
        {criticalVars.map((variable) => {
          const hypothesis = hypothesisByVar[variable.name];
          const currentParams = params[variable.name] || getTriangularParams(hypothesis);

          return (
            <TriangularSlider
              key={variable.name}
              variableName={variable.name}
              variableLabel={variable.label || variable.name}
              variableDescription={variable.description}
              initialParams={currentParams}
              onChange={(newParams) => onChange(variable.name, newParams)}
              unit={variable.unit}
              disabled={readOnly}
            />
          );
        })}
      </div>
    </div>
  );
}
