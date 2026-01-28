/**
 * StructuralAssumptionsStep component (Layer C).
 *
 * Read-only display of structural assumptions (latent variables, demographics, etc.).
 * Shows variables with controllability = 'none' | 'low' that are not outcomes.
 *
 * References:
 *   - Design: Scientific editorial style
 */

import { useMemo } from 'react';
import { FileText, Eye, ArrowRight, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Variable } from '@/types/causal-dag';
import type { Hypothesis } from '@/types/hypothesis';

interface StructuralAssumptionsStepProps {
  variables: Variable[];
  hypotheses: Hypothesis[];
  onConfirm: () => void;
  isConfirming: boolean;
  readOnly?: boolean;
}

/**
 * Distribution type labels in Portuguese.
 */
const DISTRIBUTION_LABELS: Record<string, string> = {
  uniform: 'Uniforme',
  normal: 'Normal',
  beta: 'Beta',
  lognormal: 'Log-Normal',
  bernoulli: 'Bernoulli',
  triangular: 'Triangular',
};

/**
 * Variable type labels in Portuguese.
 */
const TYPE_LABELS: Record<string, string> = {
  observable: 'Observável',
  latent: 'Latente',
  friction: 'Fricção',
  failure: 'Falha',
  process: 'Processo',
  temporal: 'Temporal',
  input: 'Entrada',
  intermediate: 'Intermediária',
  output: 'Saída',
};

/**
 * Filter variables that are structural assumptions (not controllable, not outcomes).
 */
function filterStructuralVariables(variables: Variable[]): Variable[] {
  return variables.filter(
    (v) =>
      v.controllability &&
      ['none', 'low'].includes(v.controllability) &&
      !v.is_outcome &&
      !v.is_critical_uncertainty
  );
}

/**
 * Format distribution parameters for display.
 */
function formatParameters(hypothesis: Hypothesis): string {
  const p = hypothesis.parameters;
  if (!p) return '-';

  switch (p.distribution_type) {
    case 'uniform':
      return `[${p.min_value?.toFixed(2) ?? 0}, ${p.max_value?.toFixed(2) ?? 1}]`;
    case 'normal':
      return `μ=${p.mean?.toFixed(2) ?? 0}, σ=${p.std_dev?.toFixed(2) ?? 1}`;
    case 'beta':
      return `α=${p.alpha?.toFixed(1) ?? 1}, β=${p.beta?.toFixed(1) ?? 1}`;
    case 'lognormal':
      return `μ=${p.mean?.toFixed(2) ?? 0}, σ=${p.std_dev?.toFixed(2) ?? 1}`;
    case 'bernoulli':
      return `p=${p.mean?.toFixed(2) ?? 0.5}`;
    case 'triangular':
      return `[${p.min_value?.toFixed(1)}, ${p.mode?.toFixed(1)}, ${p.max_value?.toFixed(1)}]`;
    default:
      return '-';
  }
}

/**
 * Step component showing structural assumptions (read-only) and confirm button.
 */
export function StructuralAssumptionsStep({
  variables,
  hypotheses,
  onConfirm,
  isConfirming,
  readOnly = false,
}: StructuralAssumptionsStepProps) {
  const structuralVars = useMemo(
    () => filterStructuralVariables(variables),
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

  // Separate outcomes for display
  const outcomes = useMemo(
    () => variables.filter((v) => v.is_outcome),
    [variables]
  );

  return (
    <div className="space-y-6">
      {/* Outcomes section */}
      {outcomes.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Check className="h-4 w-4 text-green-600" />
            Variáveis de Resultado
          </h3>
          <div className="grid gap-3">
            {outcomes.map((variable) => {
              const hypothesis = hypothesisByVar[variable.name];
              return (
                <Card key={variable.name} className="border-green-200 bg-green-50/50">
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-green-800 font-mono text-sm">
                          {variable.label || variable.name}
                        </span>
                        {variable.description && (
                          <p className="text-xs text-green-700 mt-0.5">
                            {variable.description}
                          </p>
                        )}
                      </div>
                      {hypothesis && (
                        <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                          {DISTRIBUTION_LABELS[hypothesis.parameters?.distribution_type] ||
                            hypothesis.parameters?.distribution_type}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Structural variables section */}
      {structuralVars.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Eye className="h-4 w-4 text-slate-500" />
            Pressupostos Estruturais
            <span className="text-xs font-normal text-slate-500">(somente leitura)</span>
          </h3>
          <div className="grid gap-2">
            {structuralVars.map((variable) => {
              const hypothesis = hypothesisByVar[variable.name];
              const distType = hypothesis?.parameters?.distribution_type;

              return (
                <Card key={variable.name} className="border-slate-200 bg-slate-50/50">
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-700 font-mono text-sm truncate">
                            {variable.label || variable.name}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {TYPE_LABELS[variable.variable_type] || variable.variable_type}
                          </Badge>
                        </div>
                        {variable.description && (
                          <p className="text-xs text-slate-500 mt-0.5 truncate">
                            {variable.description}
                          </p>
                        )}
                      </div>
                      {hypothesis && (
                        <div className="text-right flex-shrink-0">
                          <Badge variant="secondary" className="text-xs">
                            {DISTRIBUTION_LABELS[distType] || distType}
                          </Badge>
                          <p className="text-xs text-slate-500 mt-1 font-mono">
                            {formatParameters(hypothesis)}
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Summary */}
      <Card className="border-indigo-200 bg-indigo-50/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2 text-indigo-800">
            <FileText className="h-4 w-4" />
            Resumo da Configuração
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-indigo-700">
                {variables.filter((v) => ['high', 'medium'].includes(v.controllability || '')).length}
              </p>
              <p className="text-xs text-indigo-600">Controláveis</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-600">
                {variables.filter((v) => v.is_critical_uncertainty).length}
              </p>
              <p className="text-xs text-amber-600">Incertezas</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-600">
                {structuralVars.length}
              </p>
              <p className="text-xs text-slate-600">Pressupostos</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Confirm button */}
      {!readOnly && (
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onConfirm} disabled={isConfirming} className="btn-primary">
            {isConfirming ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Confirmando...
              </>
            ) : (
              <>
                Confirmar e Simular
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
