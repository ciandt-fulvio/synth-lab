/**
 * Simulations page for causal simulation system.
 *
 * Main page for creating and managing causal simulations.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Components: components/simulation/
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { QuestionInput } from '@/components/simulation/QuestionInput';
import { useSimulations } from '@/hooks/use-simulations';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { PlayCircle, Trash2, Eye, Clock, CheckCircle2, XCircle } from 'lucide-react';
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
 * Simulations page component.
 */
export default function Simulations() {
  const navigate = useNavigate();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const { data: simulations, isLoading } = useSimulations({ limit: 50 });

  const handleSimulationCreated = (simulationId: string) => {
    setShowCreateForm(false);
    // Navigate to simulation detail page
    navigate(`/simulations/${simulationId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle="Simulações Causais"
        backTo="/"
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Create simulation section */}
        <section className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-section-title">Criar Nova Simulação</h2>
              <p className="text-sm text-slate-600 mt-1">
                Transforme perguntas de negócio em projeções acionáveis
              </p>
            </div>
            <Button
              onClick={() => setShowCreateForm(!showCreateForm)}
              variant={showCreateForm ? 'outline' : 'default'}
              className={showCreateForm ? 'btn-secondary' : 'btn-primary'}
            >
              {showCreateForm ? 'Cancelar' : 'Nova Simulação'}
            </Button>
          </div>

          {showCreateForm && (
            <div className="pt-4 border-t border-slate-200">
              <QuestionInput
                onSimulationCreated={handleSimulationCreated}
                randomSeed={42}
                nWorlds={500}
              />
            </div>
          )}
        </section>

        {/* Simulations list */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-section-title">Suas Simulações</h2>
            {simulations && simulations.length > 0 && (
              <p className="text-sm text-slate-600">{simulations.length} simulação(ões)</p>
            )}
          </div>

          {isLoading ? (
            <div className="card p-8 text-center text-slate-500">
              Carregando simulações...
            </div>
          ) : !simulations || simulations.length === 0 ? (
            <div className="card p-8 text-center text-slate-500">
              <p>Nenhuma simulação ainda.</p>
              <p className="text-sm mt-2">Crie sua primeira simulação para começar.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {simulations.map((simulation) => (
                <div key={simulation.id} className="card-hover p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <StatusBadge
                          status={simulation.status}
                          config={SIMULATION_STATUS_CONFIG}
                        />
                        <span className="text-xs text-slate-500">
                          {new Date(simulation.created_at).toLocaleString()}
                        </span>
                      </div>
                      <h3 className="text-card-title mb-2">{simulation.question_text}</h3>
                      {simulation.problem_decomposition && (
                        <div className="text-sm text-slate-600 space-y-1">
                          <p>
                            <strong>Resultado:</strong>{' '}
                            {simulation.problem_decomposition.primary_outcome}
                          </p>
                          {simulation.problem_decomposition.secondary_outcomes?.length > 0 && (
                            <p>
                              <strong>Secundários:</strong>{' '}
                              {simulation.problem_decomposition.secondary_outcomes.join(', ')}
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/simulations/${simulation.id}`)}
                        className="btn-ghost-icon"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
