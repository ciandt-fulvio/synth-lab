/**
 * ControllableVariablesStep component (Layer A).
 *
 * Displays controllable variables with scenario selectors in a compact list.
 * Filters variables with controllability = 'high' | 'medium' and !is_outcome.
 *
 * Design: Scientific/editorial - clean stacked list layout.
 */

import { useMemo } from 'react';
import { Settings2, Sliders } from 'lucide-react';
import { ScenarioSelector } from './ScenarioSelector';
import type { Variable } from '@/types/causal-dag';
import type { Hypothesis } from '@/types/hypothesis';

interface ControllableVariablesStepProps {
  variables: Variable[];
  hypotheses: Hypothesis[];
  selections: Record<string, string>;
  onChange: (variableName: string, scenario: string) => void;
  readOnly?: boolean;
}

/**
 * Filter variables that are controllable (high/medium) and not outcomes.
 */
function filterControllableVariables(variables: Variable[]): Variable[] {
  return variables.filter(
    (v) =>
      v.controllability &&
      ['high', 'medium'].includes(v.controllability) &&
      !v.is_outcome
  );
}

/**
 * Step component for configuring controllable variables via scenario selection.
 */
export function ControllableVariablesStep({
  variables,
  hypotheses,
  selections,
  onChange,
  readOnly = false,
}: ControllableVariablesStepProps) {
  const controllableVars = useMemo(
    () => filterControllableVariables(variables),
    [variables]
  );

  // Create lookup for hypotheses by variable name
  const hypothesisByVar = useMemo(() => {
    const map: Record<string, Hypothesis> = {};
    for (const h of hypotheses) {
      map[h.variable_name] = h;
    }
    return map;
  }, [hypotheses]);

  if (controllableVars.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-4">
          <Settings2 className="h-6 w-6 text-slate-400" />
        </div>
        <p className="text-sm font-medium text-slate-600 text-center">
          Nenhuma variável controlável identificada
        </p>
        <p className="text-xs text-slate-400 mt-1.5 text-center max-w-xs">
          Variáveis controláveis são aquelas que você pode influenciar diretamente na simulação.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 px-1">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100">
          <Sliders className="h-4 w-4 text-amber-600" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Variáveis Controláveis</h3>
          <p className="text-xs text-slate-500">
            Selecione o cenário desejado para cada variável
          </p>
        </div>
      </div>

      {/* Variables list */}
      <div className="space-y-3">
        {controllableVars.map((variable) => {
          const hypothesis = hypothesisByVar[variable.name];
          const scenarioOptions = hypothesis?.scenario_options || [];
          const selectedScenario = selections[variable.name] || hypothesis?.selected_scenario;

          if (scenarioOptions.length === 0) {
            return (
              <div
                key={variable.name}
                className="py-4 px-5 rounded-lg bg-slate-50/50 border border-dashed border-slate-200"
              >
                <span className="text-[15px] font-medium text-slate-600">
                  {variable.label || variable.name}
                </span>
                <p className="text-xs text-slate-400 mt-1 italic">
                  Cenários não disponíveis para esta variável
                </p>
              </div>
            );
          }

          return (
            <ScenarioSelector
              key={variable.name}
              variableName={variable.name}
              variableLabel={variable.label || variable.name}
              variableDescription={variable.description}
              options={scenarioOptions}
              selectedValue={selectedScenario}
              onChange={(value) => onChange(variable.name, value)}
              disabled={readOnly}
            />
          );
        })}
      </div>
    </div>
  );
}
