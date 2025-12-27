/**
 * T027 ExperimentDetail page.
 *
 * Experiment detail view with simulations and interviews sections.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US3)
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useExperiment, useUpdateExperiment } from '@/hooks/use-experiments';
import { ExperimentForm } from '@/components/experiments/ExperimentForm';
import { NewSimulationDialog } from '@/components/experiments/NewSimulationDialog';
import { NewInterviewFromExperimentDialog } from '@/components/experiments/NewInterviewFromExperimentDialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  Calendar,
  Edit,
  FlaskConical,
  MessageSquare,
  Plus,
  Users,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentUpdate } from '@/types/experiment';

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isNewSimulationOpen, setIsNewSimulationOpen] = useState(false);
  const [isNewInterviewOpen, setIsNewInterviewOpen] = useState(false);

  // Fetch experiment
  const { data: experiment, isLoading, isError, error } = useExperiment(id ?? '');

  // Update mutation
  const updateMutation = useUpdateExperiment();

  const handleEditSubmit = async (formData: ExperimentUpdate) => {
    if (!id) return;

    try {
      await updateMutation.mutateAsync({ id, data: formData });
      setIsEditOpen(false);
      toast({
        title: 'Experimento atualizado',
        description: 'As alterações foram salvas com sucesso.',
      });
    } catch (err) {
      toast({
        title: 'Erro ao atualizar experimento',
        description: err instanceof Error ? err.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

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

  const formattedDate = formatDistanceToNow(new Date(experiment.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-purple-600"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Experimentos
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/synths')}
                className="text-gray-600 hover:text-purple-600"
                title="Catálogo de Synths"
              >
                <Users className="h-5 w-5" />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditOpen(true)}
            >
              <Edit className="w-4 h-4 mr-1" />
              Editar
            </Button>
          </div>

          <div className="mt-4">
            <h1 className="text-2xl font-bold text-gray-900">
              {experiment.name}
            </h1>
            <p className="mt-2 text-gray-600">{experiment.hypothesis}</p>
            {experiment.description && (
              <p className="mt-2 text-sm text-gray-500">
                {experiment.description}
              </p>
            )}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Criado {formattedDate}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Simulations Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-purple-500" />
              <h2 className="text-xl font-semibold text-gray-900">Simulações</h2>
              <Badge variant="secondary">
                {experiment.simulation_count}
              </Badge>
            </div>
            <Button size="sm" onClick={() => setIsNewSimulationOpen(true)}>
              <Plus className="w-4 h-4 mr-1" />
              Nova Simulacao
            </Button>
          </div>

          {experiment.simulation_count === 0 ? (
            <div className="bg-white rounded-lg border border-dashed border-gray-300 p-8 text-center">
              <FlaskConical className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">
                Nenhuma simulação ainda. Crie sua primeira para testar quantitativamente.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {experiment.simulations.map((sim) => (
                <div
                  key={sim.id}
                  className="bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => navigate(`/experiments/${id}/simulations/${sim.id}`)}
                >
                  <div className="font-medium">{sim.scenario_id || 'Cenário'}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    {sim.status === 'completed' && sim.score != null
                      ? `Score: ${sim.score}/100`
                      : sim.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Interviews Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-blue-500" />
              <h2 className="text-xl font-semibold text-gray-900">Entrevistas</h2>
              <Badge variant="secondary">
                {experiment.interview_count}
              </Badge>
            </div>
            <Button size="sm" onClick={() => setIsNewInterviewOpen(true)}>
              <Plus className="w-4 h-4 mr-1" />
              Nova Entrevista
            </Button>
          </div>

          {experiment.interview_count === 0 ? (
            <div className="bg-white rounded-lg border border-dashed border-gray-300 p-8 text-center">
              <MessageSquare className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">
                Nenhuma entrevista ainda. Crie sua primeira para coletar feedback qualitativo.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {experiment.interviews.map((interview) => (
                <div
                  key={interview.exec_id}
                  className="bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => navigate(`/experiments/${id}/interviews/${interview.exec_id}`)}
                >
                  <div className="font-medium">{interview.topic_name}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    {interview.synth_count} synth(s) • {interview.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Edit Experiment Modal */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Editar Experimento</DialogTitle>
          </DialogHeader>
          <ExperimentForm
            initialData={{
              name: experiment.name,
              hypothesis: experiment.hypothesis,
              description: experiment.description ?? undefined,
            }}
            onSubmit={handleEditSubmit}
            onCancel={() => setIsEditOpen(false)}
            isSubmitting={updateMutation.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* New Simulation Modal */}
      {experiment && (
        <NewSimulationDialog
          open={isNewSimulationOpen}
          onOpenChange={setIsNewSimulationOpen}
          experimentId={id ?? ''}
          experiment={{
            name: experiment.name,
            hypothesis: experiment.hypothesis,
            description: experiment.description,
          }}
        />
      )}

      {/* New Interview Modal */}
      <NewInterviewFromExperimentDialog
        open={isNewInterviewOpen}
        onOpenChange={setIsNewInterviewOpen}
        experimentId={id ?? ''}
      />
    </div>
  );
}
