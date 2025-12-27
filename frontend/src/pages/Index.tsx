/**
 * T024 Index page - Experiment List (Home).
 *
 * Main page showing grid of experiment cards.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US1)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ExperimentCard } from '@/components/experiments/ExperimentCard';
import { EmptyState } from '@/components/experiments/EmptyState';
import { ExperimentForm } from '@/components/experiments/ExperimentForm';
import { useExperiments, useCreateExperiment } from '@/hooks/use-experiments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plus, Users } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentCreate } from '@/types/experiment';

export default function Index() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Fetch experiments
  const { data, isLoading, isError, error } = useExperiments();
  const experiments = data?.data ?? [];

  // Create mutation
  const createMutation = useCreateExperiment();

  const handleExperimentClick = (id: string) => {
    navigate(`/experiments/${id}`);
  };

  const handleCreateClick = () => {
    setIsCreateOpen(true);
  };

  const handleCreateSubmit = async (formData: ExperimentCreate) => {
    try {
      await createMutation.mutateAsync(formData);
      setIsCreateOpen(false);
      toast({
        title: 'Experimento criado',
        description: `"${formData.name}" foi criado com sucesso.`,
      });
    } catch (err) {
      toast({
        title: 'Erro ao criar experimento',
        description: err instanceof Error ? err.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  const handleSynthsClick = () => {
    navigate('/synths');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-50 via-white to-blue-50/30 border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img
                src="/synthlab-log.png"
                alt="SynthLab Logo"
                className="h-8 w-auto logo-pulse-loop"
              />
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                SynthLab
              </h1>
              <Badge variant="secondary" className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                Beta
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSynthsClick}
              className="text-gray-600 hover:text-purple-600"
              title="Catálogo de Synths"
            >
              <Users className="h-5 w-5" />
            </Button>
          </div>
          <p className="mt-2 text-sm font-semibold text-gray-600">
            Pesquisa sintética, insights reais
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page header with create button */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Experimentos</h2>
            <p className="text-sm text-gray-600 mt-1">
              Gerencie seus experimentos e hipóteses
            </p>
          </div>
          {experiments.length > 0 && (
            <Button
              onClick={handleCreateClick}
              className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Novo Experimento
            </Button>
          )}
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-lg border p-4">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full mb-1" />
                <Skeleton className="h-4 w-2/3 mb-4" />
                <div className="flex justify-between">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="text-center py-12">
            <p className="text-red-600">
              Erro ao carregar experimentos: {error?.message || 'Erro desconhecido'}
            </p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && experiments.length === 0 && (
          <EmptyState onCreateClick={handleCreateClick} />
        )}

        {/* Experiment grid */}
        {!isLoading && !isError && experiments.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {experiments.map((experiment) => (
              <ExperimentCard
                key={experiment.id}
                experiment={experiment}
                onClick={handleExperimentClick}
              />
            ))}
          </div>
        )}
      </main>

      {/* Create Experiment Modal */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Novo Experimento</DialogTitle>
          </DialogHeader>
          <ExperimentForm
            onSubmit={handleCreateSubmit}
            onCancel={() => setIsCreateOpen(false)}
            isSubmitting={createMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
