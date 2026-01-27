/**
 * ReadyToRunStep component for simulation wizard.
 *
 * Shows summary and run button for final step before simulation execution.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { Button } from '@/components/ui/button';
import { PlayCircle, Loader2, CheckCircle2, Network, BarChart3, Target } from 'lucide-react';
import type { SimulationResponse } from '@/services/simulations-api';
import type { CausalDAG } from '@/types/causal-dag';
import type { Hypothesis } from '@/types/hypothesis';

interface ReadyToRunStepProps {
  simulation: SimulationResponse;
  dag: CausalDAG | null;
  hypotheses: Hypothesis[] | null;
  onRun: () => void;
  isRunning: boolean;
}

/**
 * Final step showing summary before running simulation.
 */
export function ReadyToRunStep({
  simulation,
  dag,
  hypotheses,
  onRun,
  isRunning,
}: ReadyToRunStepProps) {
  const nVariables = dag?.nodes?.length || 0;
  const nEdges = dag?.edges?.length || 0;
  const nHypotheses = hypotheses?.length || 0;
  const nWorlds = simulation.n_worlds || 500;

  return (
    <div className="space-y-8">
      {/* Success message */}
      <div className="flex items-start gap-4 p-4 bg-green-50 rounded-lg border border-green-200">
        <CheckCircle2 className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
        <div>
          <h2 className="text-lg font-semibold text-green-900">
            Pronto para Simular
          </h2>
          <p className="text-sm text-green-700 mt-1">
            Todas as etapas foram validadas. A simulação está pronta para ser executada.
          </p>
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Problem Summary */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-box-primary">
              <Target className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Problema</h3>
          </div>
          {simulation.problem_decomposition && (
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-slate-500">Intervenção</dt>
                <dd className="text-slate-900 font-medium mt-0.5">
                  {simulation.problem_decomposition.intervention}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Resultado Principal</dt>
                <dd className="text-slate-900 font-medium mt-0.5">
                  {simulation.problem_decomposition.primary_outcome}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Horizonte</dt>
                <dd className="text-slate-900 font-medium mt-0.5">
                  {simulation.problem_decomposition.time_horizon}
                </dd>
              </div>
            </dl>
          )}
        </div>

        {/* Model Summary */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-box-primary">
              <Network className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Modelo Causal</h3>
          </div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Variáveis</dt>
              <dd className="text-slate-900 font-medium">{nVariables}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Relações</dt>
              <dd className="text-slate-900 font-medium">{nEdges}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Versão</dt>
              <dd className="text-slate-900 font-medium">v{dag?.version || 1}</dd>
            </div>
          </dl>
        </div>

        {/* Hypotheses Summary */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-box-primary">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Hipóteses</h3>
          </div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Distribuições</dt>
              <dd className="text-slate-900 font-medium">{nHypotheses}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Mundos a simular</dt>
              <dd className="text-slate-900 font-medium">{nWorlds.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Seed</dt>
              <dd className="text-slate-900 font-medium">{simulation.random_seed || 42}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Simulation Info */}
      <div className="bg-slate-50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-700 mb-2">O que acontecerá</h3>
        <ol className="space-y-2 text-sm text-slate-600 list-decimal list-inside">
          <li>Serão gerados <strong>{nWorlds.toLocaleString()}</strong> mundos sintéticos</li>
          <li>Cada mundo terá valores amostrados das distribuições definidas</li>
          <li>Análise de sensibilidade identificará os principais drivers</li>
          <li>Modos de falha e clusters comportamentais serão detectados</li>
          <li>Insights acionáveis serão gerados automaticamente</li>
        </ol>
      </div>

      {/* Run Button */}
      <div className="flex justify-center pt-4 border-t">
        <Button
          onClick={onRun}
          disabled={isRunning}
          size="lg"
          className="btn-primary px-8"
        >
          {isRunning ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Simulando...
            </>
          ) : (
            <>
              <PlayCircle className="h-5 w-5 mr-2" />
              Rodar Simulação
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
