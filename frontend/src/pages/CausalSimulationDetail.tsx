/**
 * CausalSimulationDetail page for viewing and managing causal simulations.
 *
 * Implements a wizard flow for simulation creation with intermediate validations.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Components: components/simulation/
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { StepIndicator, getWizardSteps } from '@/components/simulation/StepIndicator';
import { QuestionValidationStep } from '@/components/simulation/QuestionValidationStep';
import { DAGValidationStep } from '@/components/simulation/DAGValidationStep';
import { HypothesisValidationStep } from '@/components/simulation/HypothesisValidationStep';
import { ReadyToRunStep } from '@/components/simulation/ReadyToRunStep';
import { PercentileChart } from '@/components/simulation/PercentileChart';
import {
  useSimulation,
  useSimulationInsights,
  useRunSimulation,
  useDeleteSimulation,
  useConfirmQuestion,
  useConfirmDAG,
  useConfirmHypotheses,
  useUpdateProblemDecomposition,
} from '@/hooks/use-simulations';
import { useDAG } from '@/hooks/use-dag';
import { useHypotheses } from '@/hooks/use-hypotheses';
import { Button } from '@/components/ui/button';
import {
  Trash2,
  Loader2,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Lightbulb,
} from 'lucide-react';
import { toast } from 'sonner';

/**
 * Status badge configuration for simulations.
 */
const SIMULATION_STATUS_CONFIG = {
  parsing: {
    label: 'Analisando',
    variant: 'info' as const,
    icon: Clock,
  },
  awaiting_question_validation: {
    label: 'Validar Pergunta',
    variant: 'warning' as const,
    icon: Clock,
  },
  dag_construction: {
    label: 'Gerando Modelo',
    variant: 'info' as const,
    icon: Clock,
  },
  awaiting_dag_validation: {
    label: 'Validar Modelo',
    variant: 'warning' as const,
    icon: Clock,
  },
  hypothesis_generation: {
    label: 'Gerando Hipóteses',
    variant: 'info' as const,
    icon: Clock,
  },
  awaiting_hypothesis_validation: {
    label: 'Validar Hipóteses',
    variant: 'warning' as const,
    icon: Clock,
  },
  ready_to_run: {
    label: 'Pronto',
    variant: 'success' as const,
    icon: CheckCircle2,
  },
  simulating: {
    label: 'Simulando',
    variant: 'warning' as const,
    icon: Clock,
  },
  completed: {
    label: 'Concluído',
    variant: 'success' as const,
    icon: CheckCircle2,
  },
  failed: {
    label: 'Falhou',
    variant: 'error' as const,
    icon: XCircle,
  },
};

/**
 * Insight type icons and labels.
 */
const INSIGHT_TYPE_CONFIG = {
  key_driver: {
    label: 'Driver Principal',
    icon: TrendingUp,
    color: 'indigo',
  },
  failure_mode: {
    label: 'Modo de Falha',
    icon: AlertTriangle,
    color: 'amber',
  },
  cluster_finding: {
    label: 'Padrão de Cluster',
    icon: Target,
    color: 'violet',
  },
  recommendation: {
    label: 'Recomendação',
    icon: Lightbulb,
    color: 'green',
  },
};

/**
 * CausalSimulationDetail page component.
 */
export default function CausalSimulationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [runResult, setRunResult] = useState<any>(null);
  const [viewedStep, setViewedStep] = useState<string | null>(null);

  // Data hooks
  const { data: simulation, isLoading: isLoadingSimulation, refetch: refetchSimulation } = useSimulation(id || '');
  const { data: dag, isLoading: isLoadingDAG } = useDAG(id || '', {
    enabled: !!id && (
      simulation?.status === 'awaiting_dag_validation' ||
      simulation?.status === 'awaiting_hypothesis_validation' ||
      simulation?.status === 'ready_to_run' ||
      simulation?.status === 'completed' ||
      viewedStep === 'dag' // Enable when viewing DAG step
    ),
  });
  const { data: hypotheses, isLoading: isLoadingHypotheses } = useHypotheses(id || '', {
    enabled: !!id && (
      simulation?.status === 'awaiting_hypothesis_validation' ||
      simulation?.status === 'ready_to_run' ||
      simulation?.status === 'completed' ||
      viewedStep === 'hypotheses' // Enable when viewing hypotheses step
    ),
  });
  const { data: insights, isLoading: isLoadingInsights } = useSimulationInsights(id || '', {
    enabled: simulation?.status === 'completed' && !!runResult,
  });

  // Mutation hooks
  const { mutate: confirmQuestion, isPending: isConfirmingQuestion } = useConfirmQuestion();
  const { mutate: confirmDAG, isPending: isConfirmingDAG } = useConfirmDAG();
  const { mutate: confirmHypotheses, isPending: isConfirmingHypotheses } = useConfirmHypotheses();
  const { mutateAsync: updateProblemDecomposition, isPending: isUpdatingProblem } = useUpdateProblemDecomposition();
  const { mutate: runSimulation, isPending: isRunning } = useRunSimulation();
  const { mutate: deleteSimulation, isPending: isDeleting } = useDeleteSimulation();

  // Handlers
  const handleConfirmQuestion = () => {
    if (!id) return;
    confirmQuestion(id, {
      onSuccess: () => {
        toast.success('Modelo causal gerado com sucesso');
        refetchSimulation();
      },
      onError: (error) => {
        toast.error('Erro ao gerar modelo causal', {
          description: error.message || 'Por favor, tente novamente.',
        });
      },
    });
  };

  const handleConfirmDAG = () => {
    if (!id) return;
    confirmDAG(id, {
      onSuccess: () => {
        toast.success('Hipóteses geradas com sucesso');
        refetchSimulation();
      },
      onError: (error) => {
        toast.error('Erro ao gerar hipóteses', {
          description: error.message || 'Por favor, tente novamente.',
        });
      },
    });
  };

  const handleConfirmHypotheses = () => {
    if (!id) return;
    confirmHypotheses(id, {
      onSuccess: () => {
        toast.success('Simulação pronta para execução');
        refetchSimulation();
      },
      onError: (error) => {
        toast.error('Erro ao confirmar hipóteses', {
          description: error.message || 'Por favor, tente novamente.',
        });
      },
    });
  };

  const handleUpdateProblemDecomposition = async (update: any) => {
    if (!id) return;
    await updateProblemDecomposition({ simulationId: id, update });
    refetchSimulation();
  };

  const handleRun = () => {
    if (!id) return;
    runSimulation(
      { simulationId: id },
      {
        onSuccess: (data) => {
          setRunResult(data);
          toast.success('Simulação concluída', {
            description: `Gerados ${data.n_worlds} mundos e ${data.n_insights} insights.`,
          });
          refetchSimulation();
        },
        onError: (error) => {
          toast.error('Simulação falhou', {
            description: error.message || 'Por favor, tente novamente.',
          });
        },
      }
    );
  };

  const handleDelete = () => {
    if (!id) return;
    if (confirm('Tem certeza que deseja excluir esta simulação?')) {
      deleteSimulation(id, {
        onSuccess: () => {
          toast.success('Simulação excluída');
          navigate('/simulations');
        },
        onError: (error) => {
          toast.error('Erro ao excluir simulação', {
            description: error.message,
          });
        },
      });
    }
  };

  // Loading state
  if (isLoadingSimulation) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Carregando..." backTo="/simulations" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center text-slate-500">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            Carregando simulação...
          </div>
        </main>
      </div>
    );
  }

  // Not found state
  if (!simulation) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Não Encontrado" backTo="/simulations" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center text-slate-500">Simulação não encontrada</div>
        </main>
      </div>
    );
  }

  const steps = getWizardSteps(simulation.status);
  const hasResults = !!runResult;

  // Handle step click - navigate to that step
  const handleStepClick = (stepId: string) => {
    // Get the current step based on simulation status
    const statusToStep: Record<string, string> = {
      awaiting_question_validation: 'question',
      awaiting_dag_validation: 'dag',
      awaiting_hypothesis_validation: 'hypotheses',
      ready_to_run: 'run',
    };
    const currentStepId = statusToStep[simulation.status];

    // If clicking the current step, clear viewedStep to show current content
    if (stepId === currentStepId) {
      setViewedStep(null);
    } else {
      setViewedStep(stepId);
    }
  };

  // Render content based on viewed step or current status
  const renderStepContent = () => {
    // If viewing a previous step, render it in read-only mode
    if (viewedStep) {
      switch (viewedStep) {
        case 'question':
          return simulation.problem_decomposition ? (
            <QuestionValidationStep
              problemDecomposition={simulation.problem_decomposition}
              onConfirm={() => {}}
              onUpdate={async () => {}}
              isConfirming={false}
              isUpdating={false}
              readOnly
            />
          ) : null;

        case 'dag':
          return (
            <DAGValidationStep
              simulationId={id!}
              dag={dag || null}
              isLoading={isLoadingDAG}
              onConfirm={() => {}}
              isConfirming={false}
              readOnly
            />
          );

        case 'hypotheses':
          return (
            <HypothesisValidationStep
              simulationId={id!}
              hypotheses={hypotheses || null}
              dag={dag || null}
              isLoading={isLoadingHypotheses}
              onConfirm={() => {}}
              isConfirming={false}
              readOnly
            />
          );

        default:
          return null;
      }
    }

    // Otherwise, render based on current status
    switch (simulation.status) {
      case 'awaiting_question_validation':
        return simulation.problem_decomposition ? (
          <QuestionValidationStep
            problemDecomposition={simulation.problem_decomposition}
            onConfirm={handleConfirmQuestion}
            onUpdate={handleUpdateProblemDecomposition}
            isConfirming={isConfirmingQuestion}
            isUpdating={isUpdatingProblem}
          />
        ) : null;

      case 'awaiting_dag_validation':
        return (
          <DAGValidationStep
            simulationId={id!}
            dag={dag || null}
            isLoading={isLoadingDAG}
            onConfirm={handleConfirmDAG}
            isConfirming={isConfirmingDAG}
          />
        );

      case 'awaiting_hypothesis_validation':
        return (
          <HypothesisValidationStep
            simulationId={id!}
            hypotheses={hypotheses || null}
            dag={dag || null}
            isLoading={isLoadingHypotheses}
            onConfirm={handleConfirmHypotheses}
            isConfirming={isConfirmingHypotheses}
          />
        );

      case 'ready_to_run':
        return (
          <ReadyToRunStep
            simulation={simulation}
            dag={dag || null}
            hypotheses={hypotheses || null}
            onRun={handleRun}
            isRunning={isRunning}
          />
        );

      case 'completed':
        return hasResults ? (
          <>
            {/* Outcome distributions */}
            <section className="card p-6">
              <PercentileChart distributions={runResult.outcome_distributions} />
            </section>

            {/* Insights */}
            {insights && insights.length > 0 && (
              <section className="space-y-4">
                <h2 className="text-section-title">Insights</h2>
                <div className="grid grid-cols-1 gap-4">
                  {insights.map((insight) => {
                    const config = INSIGHT_TYPE_CONFIG[insight.insight_type];
                    const Icon = config.icon;

                    return (
                      <div key={insight.id} className="card p-6">
                        <div className="flex items-start gap-4">
                          <div
                            className={`icon-box-${
                              config.color === 'indigo' ? 'primary' : 'neutral'
                            } flex-shrink-0`}
                          >
                            <Icon className="h-5 w-5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span
                                className={`badge-${
                                  config.color === 'green'
                                    ? 'success'
                                    : config.color === 'amber'
                                    ? 'warning'
                                    : 'info'
                                }`}
                              >
                                {config.label}
                              </span>
                            </div>
                            <h3 className="text-card-title mb-2">{insight.title}</h3>
                            <p className="text-body mb-4">{insight.description}</p>

                            {insight.recommended_actions.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="text-sm font-semibold text-slate-700">
                                  Ações Recomendadas:
                                </h4>
                                <ul className="space-y-2">
                                  {insight.recommended_actions.map((action, idx) => (
                                    <li key={idx} className="flex items-start gap-3">
                                      <span
                                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                                          action.priority === 'high'
                                            ? 'bg-red-100 text-red-700'
                                            : action.priority === 'medium'
                                            ? 'bg-amber-100 text-amber-700'
                                            : 'bg-slate-100 text-slate-700'
                                        }`}
                                      >
                                        {action.priority === 'high'
                                          ? 'alta'
                                          : action.priority === 'medium'
                                          ? 'média'
                                          : 'baixa'}
                                      </span>
                                      <div className="flex-1">
                                        <p className="text-sm text-slate-900">{action.action}</p>
                                        <p className="text-xs text-slate-600 mt-1">
                                          {action.rationale}
                                        </p>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </>
        ) : (
          <ReadyToRunStep
            simulation={simulation}
            dag={dag || null}
            hypotheses={hypotheses || null}
            onRun={handleRun}
            isRunning={isRunning}
          />
        );

      case 'simulating':
        return (
          <div className="card p-8 text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Simulação em Progresso</h3>
            <p className="text-sm text-slate-600">
              Gerando {simulation.n_worlds || 500} mundos sintéticos...
            </p>
          </div>
        );

      case 'dag_construction':
      case 'hypothesis_generation':
        return (
          <div className="card p-8 text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              {simulation.status === 'dag_construction'
                ? 'Gerando Modelo Causal'
                : 'Gerando Hipóteses'}
            </h3>
            <p className="text-sm text-slate-600">Por favor, aguarde...</p>
          </div>
        );

      case 'failed':
        return (
          <div className="card p-8 text-center">
            <XCircle className="h-12 w-12 mx-auto mb-4 text-red-500" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Simulação Falhou</h3>
            <p className="text-sm text-slate-600">{simulation.error_message || 'Erro desconhecido'}</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={simulation.question_text}
        backTo="/simulations"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="btn-ghost-icon"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Status and Progress */}
        <section className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <StatusBadge status={simulation.status} config={SIMULATION_STATUS_CONFIG} />
              <span className="text-xs text-slate-500">
                Criado em {new Date(simulation.created_at).toLocaleString('pt-BR')}
              </span>
            </div>
          </div>

          {/* Step Indicator (only show for wizard steps) */}
          {['awaiting_question_validation', 'awaiting_dag_validation', 'awaiting_hypothesis_validation', 'ready_to_run'].includes(simulation.status) && (
            <StepIndicator
              steps={steps}
              viewedStep={viewedStep}
              onStepClick={handleStepClick}
            />
          )}
        </section>

        {/* Step Content */}
        <section className="card p-6">{renderStepContent()}</section>
      </main>
    </div>
  );
}
