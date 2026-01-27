/**
 * HypothesisValidationStep component for simulation wizard.
 *
 * Displays the generated hypotheses for user review with link to full editor.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { HypothesisTable } from '@/components/simulation/HypothesisTable';
import { ArrowRight, Edit2, Loader2, BarChart3, AlertTriangle } from 'lucide-react';
import type { Hypothesis } from '@/types/hypothesis';

interface HypothesisValidationStepProps {
  simulationId: string;
  hypotheses: Hypothesis[] | null;
  isLoading: boolean;
  onConfirm: () => void;
  isConfirming: boolean;
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
};

/**
 * Step component for validating the generated hypotheses.
 */
export function HypothesisValidationStep({
  simulationId,
  hypotheses,
  isLoading,
  onConfirm,
  isConfirming,
}: HypothesisValidationStepProps) {
  const navigate = useNavigate();

  const handleEditHypotheses = () => {
    navigate(`/simulations/${simulationId}/hypotheses`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Hipóteses não encontradas</h3>
        <p className="text-sm text-slate-600">
          As hipóteses ainda não foram geradas para esta simulação.
        </p>
      </div>
    );
  }

  // Group by distribution type for summary
  const distributionCounts = hypotheses.reduce((acc, h) => {
    const distType = h.parameters?.distribution_type || 'unknown';
    acc[distType] = (acc[distType] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Validar Hipóteses</h2>
          <p className="text-sm text-slate-600 mt-1">
            Revise as distribuições de probabilidade geradas. Você pode ajustar os parâmetros antes
            de executar a simulação.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleEditHypotheses}>
          <Edit2 className="h-4 w-4 mr-1" />
          Editar Hipóteses
        </Button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-50 rounded-lg p-4 text-center">
          <BarChart3 className="h-5 w-5 mx-auto text-indigo-600 mb-2" />
          <p className="text-2xl font-bold text-slate-900">{hypotheses.length}</p>
          <p className="text-xs text-slate-600">Variáveis</p>
        </div>
        {Object.entries(distributionCounts).slice(0, 3).map(([type, count]) => (
          <div key={type} className="bg-slate-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{count}</p>
            <p className="text-xs text-slate-600">{DISTRIBUTION_LABELS[type] || type}</p>
          </div>
        ))}
      </div>

      {/* Hypotheses Table Preview */}
      <div className="border rounded-lg overflow-hidden">
        <div className="p-4 border-b bg-slate-50">
          <h3 className="text-sm font-medium text-slate-700">Distribuições de Probabilidade</h3>
        </div>
        <div className="max-h-[400px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-700">Variável</th>
                <th className="px-4 py-3 text-left font-medium text-slate-700">Distribuição</th>
                <th className="px-4 py-3 text-left font-medium text-slate-700">Parâmetros</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {hypotheses.map((hypothesis) => {
                const distType = hypothesis.parameters?.distribution_type || 'unknown';
                return (
                  <tr key={hypothesis.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <span className="font-medium text-slate-900">{hypothesis.variable_name}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded bg-indigo-50 text-indigo-700 text-xs font-medium">
                        {DISTRIBUTION_LABELS[distType] || distType}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {formatParameters(distType, hypothesis.parameters)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Correlations Preview */}
      {hypotheses.some((h) => h.correlations && h.correlations.length > 0) && (
        <div className="border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Correlações Sugeridas</h3>
          <div className="space-y-2">
            {hypotheses
              .filter((h) => h.correlations && h.correlations.length > 0)
              .flatMap((h) =>
                h.correlations!.map((corr, idx) => (
                  <div
                    key={`${h.id}-${idx}`}
                    className="flex items-center gap-2 text-sm text-slate-600"
                  >
                    <span className="font-medium">{h.variable_name}</span>
                    <span className="text-slate-400">↔</span>
                    <span className="font-medium">{corr.with_variable_name}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        corr.correlation > 0.5
                          ? 'bg-green-100 text-green-700'
                          : corr.correlation < -0.5
                          ? 'bg-red-100 text-red-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      r = {corr.correlation.toFixed(2)}
                    </span>
                  </div>
                ))
              )}
          </div>
        </div>
      )}

      <div className="flex justify-end pt-4 border-t">
        <Button onClick={onConfirm} disabled={isConfirming} className="btn-primary">
          {isConfirming ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Confirmando...
            </>
          ) : (
            <>
              Confirmar Hipóteses
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * Format distribution parameters for display.
 */
function formatParameters(type: string, params: Record<string, number | string | null | undefined> | null): string {
  if (!params) return '-';

  switch (type) {
    case 'uniform':
      return `[${params.low?.toFixed(2) || 0}, ${params.high?.toFixed(2) || 1}]`;
    case 'normal':
      return `μ=${params.mean?.toFixed(2) || 0}, σ=${params.std?.toFixed(2) || 1}`;
    case 'beta':
      return `α=${params.alpha?.toFixed(1) || 1}, β=${params.beta?.toFixed(1) || 1}`;
    case 'lognormal':
      return `μ=${params.mean?.toFixed(2) || 0}, σ=${params.sigma?.toFixed(2) || 1}`;
    case 'bernoulli':
      return `p=${params.p?.toFixed(2) || 0.5}`;
    default:
      return JSON.stringify(params);
  }
}
