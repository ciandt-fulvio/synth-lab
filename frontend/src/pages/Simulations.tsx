/**
 * Simulations page for causal simulation system.
 *
 * Streamlined page with inline question input and clean simulation list.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Components: components/simulation/
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useSimulations, useCreateSimulation } from '@/hooks/use-simulations';
import { StatusBadge } from '@/components/shared/StatusBadge';
import {
  Loader2,
  Sparkles,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  FlaskConical,
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
    label: 'Refinamento',
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

const PLACEHOLDER_EXAMPLES = [
  'Qual será a taxa de adoção de um serviço de assinatura semanal de refeições?',
  'Quantos usuários vão converter do plano gratuito para o pago no Q1?',
  'Qual é a receita esperada do lançamento de uma nova feature premium?',
];

/**
 * Simulations page component.
 */
export default function Simulations() {
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [placeholderIdx] = useState(() => Math.floor(Math.random() * PLACEHOLDER_EXAMPLES.length));
  const { data: simulations, isLoading } = useSimulations({ limit: 50 });
  const { mutate: createSimulation, isPending: isCreating } = useCreateSimulation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length < 10) {
      toast.error('Pergunta muito curta', {
        description: 'A pergunta deve ter pelo menos 10 caracteres.',
      });
      return;
    }

    createSimulation(
      { question_text: trimmed, random_seed: 42, n_worlds: 500 },
      {
        onSuccess: (data) => {
          toast.success('Simulação criada');
          navigate(`/simulations/${data.id}`);
        },
        onError: (error) => {
          toast.error('Erro ao criar simulação', {
            description: error.message || 'Tente novamente.',
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Simulações Causais" backTo="/" />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Compact question input */}
        <form onSubmit={handleSubmit} className="card p-3">
          <div className="flex items-center gap-3">
            <div className="icon-box-light flex-shrink-0">
              <Sparkles className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={PLACEHOLDER_EXAMPLES[placeholderIdx]}
              disabled={isCreating}
              className="flex-1 text-sm bg-transparent border-none outline-none placeholder:text-slate-400 text-slate-900 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isCreating || question.trim().length < 10}
              className="btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isCreating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Simular'
              )}
            </button>
          </div>
        </form>

        {/* Simulations list */}
        {isLoading ? (
          <div className="card p-8 text-center text-slate-500">
            <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
            <p className="text-sm">Carregando...</p>
          </div>
        ) : !simulations || simulations.length === 0 ? (
          <div className="card p-12 text-center">
            <div className="icon-box-neutral mx-auto mb-4 w-fit">
              <FlaskConical className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium text-slate-700 mb-1">Nenhuma simulação ainda</p>
            <p className="text-xs text-slate-500">
              Digite uma pergunta de negócio acima para criar sua primeira simulação.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-1">
              {simulations.length} simulação{simulations.length !== 1 ? 'ões' : ''}
            </p>
            <div className="space-y-1">
              {simulations.map((simulation) => (
                <button
                  key={simulation.id}
                  type="button"
                  onClick={() => navigate(`/simulations/${simulation.id}`)}
                  className="w-full text-left card-hover p-4 flex items-center gap-4 group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {simulation.question_text}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5">
                      <StatusBadge
                        status={simulation.status}
                        config={SIMULATION_STATUS_CONFIG}
                      />
                      <span className="text-xs text-slate-400">
                        {new Date(simulation.created_at).toLocaleDateString('pt-BR', {
                          day: '2-digit',
                          month: 'short',
                        })}
                      </span>
                      {simulation.problem_decomposition && (
                        <span className="text-xs text-slate-400 hidden sm:inline truncate max-w-[200px]">
                          {simulation.problem_decomposition.primary_outcome}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-slate-500 flex-shrink-0 transition-colors" />
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
