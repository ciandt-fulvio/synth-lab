/**
 * T034 SimulationDetail page.
 *
 * Simulation detail view within experiment context.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US6)
 */

import { useParams, useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useExperiment } from '@/hooks/use-experiments';
import {
  ArrowLeft,
  FlaskConical,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  BarChart3,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function SimulationDetail() {
  const { id: expId, simId } = useParams<{ id: string; simId: string }>();
  const navigate = useNavigate();

  // Fetch experiment to get simulation details
  const { data: experiment, isLoading, isError, error } = useExperiment(expId ?? '');

  // Find the simulation in the experiment's simulations array
  const simulation = experiment?.simulations.find(s => s.id === simId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Skeleton className="h-48 w-full" />
        </main>
      </div>
    );
  }

  if (isError || !experiment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Experimento não encontrado
          </h2>
          <p className="text-gray-600 mb-4">
            {error?.message || 'O experimento solicitado não existe.'}
          </p>
          <Button onClick={() => navigate('/')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar para experimentos
          </Button>
        </div>
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Simulação não encontrada
          </h2>
          <p className="text-gray-600 mb-4">
            A simulação solicitada não existe neste experimento.
          </p>
          <Button onClick={() => navigate(`/experiments/${expId}`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar para {experiment.name}
          </Button>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Concluída
          </Badge>
        );
      case 'running':
        return (
          <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
            <Clock className="w-3 h-3 mr-1 animate-spin" />
            Em execução
          </Badge>
        );
      case 'failed':
        return (
          <Badge className="bg-red-100 text-red-700 hover:bg-red-100">
            <XCircle className="w-3 h-3 mr-1" />
            Falhou
          </Badge>
        );
      default:
        return (
          <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-100">
            <AlertCircle className="w-3 h-3 mr-1" />
            Pendente
          </Badge>
        );
    }
  };

  const formattedStartDate = simulation.started_at
    ? formatDistanceToNow(new Date(simulation.started_at), {
        addSuffix: true,
        locale: ptBR,
      })
    : 'Não iniciada';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/experiments/${expId}`)}
              className="text-gray-600 hover:text-purple-600"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              {experiment.name}
            </Button>
          </div>

          <div className="mt-4 flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <FlaskConical className="h-6 w-6 text-purple-500" />
                <h1 className="text-2xl font-bold text-gray-900">
                  Simulação: {simulation.scenario_id}
                </h1>
                {getStatusBadge(simulation.status)}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Iniciada {formattedStartDate}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Score Section */}
        {simulation.status === 'completed' && simulation.score != null && (
          <section className="bg-white rounded-lg border p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="h-5 w-5 text-purple-500" />
              <h2 className="text-xl font-semibold text-gray-900">Resultado</h2>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold text-purple-600">
                {simulation.score}
                <span className="text-lg text-gray-500">/100</span>
              </div>
              {simulation.has_insights && (
                <Badge className="bg-purple-100 text-purple-700">
                  Insights disponíveis
                </Badge>
              )}
            </div>
          </section>
        )}

        {/* Placeholder for detailed analysis */}
        <section className="bg-white rounded-lg border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Análise Detalhada
          </h2>
          <div className="text-center py-8 text-gray-500">
            <FlaskConical className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>
              A análise detalhada com gráficos e insights estará disponível em breve.
            </p>
            <p className="text-sm mt-2">
              Use a API diretamente para acessar os dados de simulação avançados.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
