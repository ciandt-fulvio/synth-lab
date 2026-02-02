/**
 * HypothesisWizard page for simplified hypothesis generation.
 *
 * Implements a 2-step wizard flow:
 * 1. Scenario Profile Selection (Conservative/Realistic/Optimistic)
 * 2. Review Generated Hypotheses
 *
 * References:
 * - Spec: specs/036-simplified-hypothesis-wizard/spec.md
 * - Components: components/simulation/hypothesis/
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import {
  ScenarioProfileSelector,
  ClarificationQuestionsStep,
  HypothesisReviewStep,
  type ClarificationResponse,
} from '@/components/simulation/hypothesis';
import { useSimulation } from '@/hooks/use-simulations';
import { useDAG } from '@/hooks/use-dag';
import { useInitWizard, useApplyClarifications } from '@/hooks/use-hypothesis-wizard';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowRight, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import type {
  ScenarioProfile,
  ClarificationQuestion,
} from '@/services/hypothesis-wizard-api';
import type { Hypothesis } from '@/types/hypothesis';

type WizardStep = 'profile' | 'clarification' | 'review';

/**
 * Simplified hypothesis wizard page.
 */
export default function HypothesisWizard() {
  const { simulationId } = useParams<{ simulationId: string }>();
  const navigate = useNavigate();

  // Wizard state
  const [currentStep, setCurrentStep] = useState<WizardStep>('profile');
  const [selectedProfile, setSelectedProfile] = useState<ScenarioProfile>('realistic');
  const [generatedHypotheses, setGeneratedHypotheses] = useState<Hypothesis[] | null>(null);
  const [clarificationQuestions, setClarificationQuestions] = useState<
    ClarificationQuestion[] | null
  >(null);
  const [highUncertaintyVars, setHighUncertaintyVars] = useState<string[]>([]);

  // Fetch simulation data
  const { data: simulation, isLoading: isLoadingSimulation } = useSimulation(simulationId!);
  const { data: dag, isLoading: isLoadingDAG } = useDAG(simulationId!);

  // Initialize wizard mutation
  const {
    mutate: initialize,
    isPending: isInitializing,
  } = useInitWizard();

  // Apply clarifications mutation
  const {
    mutate: applyClarifications,
    isPending: isApplying,
  } = useApplyClarifications();

  /**
   * Handle scenario profile selection and initialization.
   */
  const handleInitialize = () => {
    if (!simulationId) return;

    initialize(
      {
        simulationId,
        request: { scenario_profile: selectedProfile },
      },
      {
        onSuccess: (data) => {
          setGeneratedHypotheses(data.hypotheses);
          setClarificationQuestions(data.clarification_questions);

          // Go to clarification step if there are questions, otherwise go to review
          if (data.clarification_questions && data.clarification_questions.length > 0) {
            setCurrentStep('clarification');
          } else {
            setCurrentStep('review');
          }

          toast.success('Hipóteses geradas com sucesso', {
            description: `${data.hypotheses.length} hipóteses criadas com perfil ${
              selectedProfile === 'conservative'
                ? 'Conservador'
                : selectedProfile === 'realistic'
                ? 'Realista'
                : 'Otimista'
            }`,
          });
        },
        onError: (error) => {
          toast.error('Erro ao gerar hipóteses', {
            description: error instanceof Error ? error.message : 'Erro desconhecido',
          });
        },
      }
    );
  };

  /**
   * Handle clarification responses submission.
   */
  const handleClarificationSubmit = (responses: ClarificationResponse[]) => {
    if (!simulationId) return;

    applyClarifications(
      {
        simulationId,
        request: { responses },
      },
      {
        onSuccess: (data) => {
          setGeneratedHypotheses(data.hypotheses);
          setHighUncertaintyVars([]); // Clarifications answered - no high uncertainty
          setCurrentStep('review');
          toast.success('Hipóteses ajustadas!', {
            description: `${responses.length} variáveis refinadas`,
          });
        },
        onError: (error) => {
          toast.error('Erro ao aplicar ajustes', {
            description: error instanceof Error ? error.message : 'Erro desconhecido',
          });
        },
      }
    );
  };

  /**
   * Skip clarification questions and go directly to review.
   */
  const handleSkipClarification = () => {
    // Track which variables have high uncertainty (all clarification question variables)
    if (clarificationQuestions) {
      setHighUncertaintyVars(clarificationQuestions.map((q) => q.variable_name));
    }
    setCurrentStep('review');
    toast.info('Perguntas puladas', {
      description: 'Usando hipóteses geradas pelo perfil de cenário',
    });
  };

  /**
   * Handle completion and navigation to simulation detail.
   */
  const handleComplete = () => {
    toast.success('Hipóteses configuradas!', {
      description: 'Você pode agora executar a simulação',
    });
    navigate(`/simulations/${simulationId}`);
  };

  // Loading state
  if (isLoadingSimulation || isLoadingDAG) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Wizard de Hipóteses" backTo={`/simulations/${simulationId}`} />
        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        </main>
      </div>
    );
  }

  // No simulation found
  if (!simulation) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Wizard de Hipóteses" backTo="/simulations" />
        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <p className="text-slate-600">Simulação não encontrada</p>
          </div>
        </main>
      </div>
    );
  }

  // DAG validation check
  if (!dag || !dag.is_validated) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Wizard de Hipóteses" backTo={`/simulations/${simulationId}`} />
        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="card p-8 text-center">
              <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
              <h2 className="text-xl font-semibold text-slate-900 mb-2">
                DAG ainda não validado
              </h2>
              <p className="text-slate-600 mb-6">
                O wizard de hipóteses só pode ser usado depois que o modelo causal (DAG) for
                validado. Volte para a página da simulação e complete as etapas anteriores.
              </p>
              <Button onClick={() => navigate(`/simulations/${simulationId}`)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Voltar para Simulação
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle="Wizard de Hipóteses"
        backTo={`/simulations/${simulationId}`}
      />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Simulation info */}
        <div className="mb-8">
          <h1 className="text-page-title mb-2">{simulation.name}</h1>
          <p className="text-slate-600">{simulation.description || 'Sem descrição'}</p>
        </div>

        {/* Step indicator */}
        <div className="mb-8">
          <div className="flex items-center gap-4">
            {/* Step 1: Profile */}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-semibold',
                  currentStep === 'profile'
                    ? 'border-indigo-600 bg-indigo-600 text-white'
                    : currentStep === 'clarification' || currentStep === 'review'
                    ? 'border-green-600 bg-green-600 text-white'
                    : 'border-slate-300 bg-white text-slate-400'
                )}
              >
                {currentStep === 'clarification' || currentStep === 'review' ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  '1'
                )}
              </div>
              <span
                className={cn(
                  'text-sm font-medium',
                  currentStep === 'profile' ? 'text-slate-900' : 'text-slate-600'
                )}
              >
                Perfil de Cenário
              </span>
            </div>

            {/* Connector */}
            <div className="flex-1 h-0.5 bg-slate-200" />

            {/* Step 2: Clarification (optional) */}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-semibold',
                  currentStep === 'clarification'
                    ? 'border-indigo-600 bg-indigo-600 text-white'
                    : currentStep === 'review'
                    ? 'border-green-600 bg-green-600 text-white'
                    : 'border-slate-300 bg-white text-slate-400'
                )}
              >
                {currentStep === 'review' ? <CheckCircle2 className="h-4 w-4" /> : '2'}
              </div>
              <span
                className={cn(
                  'text-sm font-medium',
                  currentStep === 'clarification' ? 'text-slate-900' : 'text-slate-400'
                )}
              >
                Perguntas (opcional)
              </span>
            </div>

            {/* Connector */}
            <div className="flex-1 h-0.5 bg-slate-200" />

            {/* Step 3: Review */}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-semibold',
                  currentStep === 'review'
                    ? 'border-indigo-600 bg-indigo-600 text-white'
                    : 'border-slate-300 bg-white text-slate-400'
                )}
              >
                3
              </div>
              <span
                className={cn(
                  'text-sm font-medium',
                  currentStep === 'review' ? 'text-slate-900' : 'text-slate-400'
                )}
              >
                Revisar Hipóteses
              </span>
            </div>
          </div>
        </div>

        {/* Step content */}
        <div className="space-y-6">
          {currentStep === 'profile' && (
            <>
              {/* Profile selector */}
              <div className="card">
                <ScenarioProfileSelector
                  value={selectedProfile}
                  onChange={setSelectedProfile}
                  disabled={isInitializing}
                />
              </div>

              {/* Action buttons */}
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate(`/simulations/${simulationId}`)}
                  disabled={isInitializing}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleInitialize}
                  disabled={isInitializing}
                  className="btn-primary"
                >
                  {isInitializing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Gerando...
                    </>
                  ) : (
                    <>
                      Gerar Hipóteses
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </>
          )}

          {currentStep === 'clarification' && clarificationQuestions && (
            <>
              <ClarificationQuestionsStep
                questions={clarificationQuestions}
                onSubmit={handleClarificationSubmit}
                onSkip={handleSkipClarification}
                disabled={isApplying}
              />
            </>
          )}

          {currentStep === 'review' && generatedHypotheses && (
            <>
              {/* Hypotheses review with uncertainty indicators */}
              <HypothesisReviewStep
                hypotheses={generatedHypotheses}
                highUncertaintyVars={highUncertaintyVars}
              />

              {/* Action buttons */}
              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep('profile')}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Voltar
                </Button>
                <div className="flex gap-3">
                  {highUncertaintyVars.length > 0 && clarificationQuestions && (
                    <Button
                      variant="outline"
                      onClick={() => {
                        setHighUncertaintyVars([]);
                        setCurrentStep('clarification');
                      }}
                    >
                      Responder Perguntas
                    </Button>
                  )}
                  <Button onClick={handleComplete} className="btn-primary">
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Concluir
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
