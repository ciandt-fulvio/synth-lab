/**
 * RefinementStep component for simulation wizard.
 *
 * Combines clarification questions and run summary into a single step.
 * Replaces HypothesisValidationStep (4 sub-steps) + ReadyToRunStep.
 *
 * References:
 *   - Spec: specs/036-simplified-hypothesis-wizard/spec.md
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { PlayCircle, Loader2, CheckCircle2, Network, BarChart3, Target } from 'lucide-react';
import { ClarificationQuestionsStep } from '@/components/simulation/hypothesis/ClarificationQuestionsStep';
import type { ClarificationQuestion } from '@/services/simulations-api';
import type { SimulationResponse } from '@/services/simulations-api';
import type { CausalDAG } from '@/types/causal-dag';
import type { Hypothesis } from '@/types/hypothesis';
import type { ClarificationResponse } from '@/components/simulation/hypothesis/ClarificationQuestionsStep';
import type { ResponseType } from '@/services/hypothesis-wizard-api';

interface RefinementStepProps {
  simulationId: string;
  simulation: SimulationResponse;
  hypotheses: Hypothesis[] | null;
  dag: CausalDAG | null;
  clarificationQuestions: ClarificationQuestion[];
  onClarify: (responses: ClarificationResponse[]) => void;
  onRun: () => void;
  isRunning: boolean;
  isClarifying?: boolean;
}

/**
 * Refinement step: clarification questions + summary + run button.
 */
export function RefinementStep({
  simulation,
  hypotheses,
  dag,
  clarificationQuestions,
  onClarify,
  onRun,
  isRunning,
  isClarifying = false,
}: RefinementStepProps) {
  const [clarificationsDone, setClarificationsDone] = useState(
    clarificationQuestions.length === 0
  );

  const handleClarifySubmit = (responses: ClarificationResponse[]) => {
    onClarify(responses);
    setClarificationsDone(true);
  };

  const handleClarifySkip = () => {
    setClarificationsDone(true);
  };

  // Show clarification questions if not done yet
  if (!clarificationsDone && clarificationQuestions.length > 0) {
    // Map ClarificationQuestion to the format expected by ClarificationQuestionsStep
    const wizardQuestions = clarificationQuestions.map((q) => ({
      variable_name: q.variable_name,
      question_text: q.question_text,
      criticality_score: q.criticality_score,
    }));

    return (
      <ClarificationQuestionsStep
        questions={wizardQuestions}
        onSubmit={handleClarifySubmit}
        onSkip={handleClarifySkip}
        disabled={isClarifying}
      />
    );
  }

  // Show summary + run button
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
            Hipóteses geradas com sucesso. Revise o resumo e execute a simulação.
          </p>
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-box-primary">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Simulação</h3>
          </div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Distribuições</dt>
              <dd className="text-slate-900 font-medium">{nHypotheses}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Mundos</dt>
              <dd className="text-slate-900 font-medium">{nWorlds.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Seed</dt>
              <dd className="text-slate-900 font-medium">{simulation.random_seed || 42}</dd>
            </div>
          </dl>
        </div>
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
              Executar Simulação
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
