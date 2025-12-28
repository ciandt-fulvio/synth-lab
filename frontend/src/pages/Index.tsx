/**
 * T024 Index page - Experiment List (Home).
 *
 * Main page showing grid of experiment cards.
 * Research Observatory aesthetic with animated elements.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US1)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Plus, Users, FlaskConical, Sparkles } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentCreate } from '@/types/experiment';

// =============================================================================
// Animated Section Component
// =============================================================================

interface AnimatedSectionProps {
  children: React.ReactNode;
  delay?: number;
}

function AnimatedSection({ children, delay = 0 }: AnimatedSectionProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`transition-all duration-500 ease-out ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      {children}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleSynthsClick}
            className="btn-secondary"
          >
            <Users className="h-4 w-4 mr-2" />
            Synths
          </Button>
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <AnimatedSection delay={0}>
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl text-white shadow-lg shadow-purple-200">
                <FlaskConical className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Experimentos</h2>
                <p className="text-sm text-slate-500">
                  Gerencie seus experimentos e hipóteses de pesquisa
                </p>
              </div>
            </div>
            {experiments.length > 0 && (
              <Button
                onClick={handleCreateClick}
                className="btn-primary"
              >
                <Plus className="w-4 h-4 mr-2" />
                Novo Experimento
              </Button>
            )}
          </div>
        </AnimatedSection>

        {/* Stats Summary */}
        {!isLoading && !isError && experiments.length > 0 && (
          <AnimatedSection delay={100}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <FlaskConical className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{experiments.length}</p>
                    <p className="text-xs text-slate-500 uppercase tracking-wide">Experimentos</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Sparkles className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {experiments.filter((e) => e.interview_count > 0).length}
                    </p>
                    <p className="text-xs text-slate-500 uppercase tracking-wide">Com Entrevistas</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {experiments.reduce((acc, e) => acc + e.interview_count, 0)}
                    </p>
                    <p className="text-xs text-slate-500 uppercase tracking-wide">Total Entrevistas</p>
                  </div>
                </div>
              </div>
            </div>
          </AnimatedSection>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <Skeleton className="h-6 w-3/4 mb-3" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3 mb-4" />
                <div className="flex justify-between pt-3 border-t border-slate-100">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && (
          <AnimatedSection delay={0}>
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600 font-medium">
                Erro ao carregar experimentos: {error?.message || 'Erro desconhecido'}
              </p>
            </div>
          </AnimatedSection>
        )}

        {/* Empty state */}
        {!isLoading && !isError && experiments.length === 0 && (
          <AnimatedSection delay={0}>
            <EmptyState onCreateClick={handleCreateClick} />
          </AnimatedSection>
        )}

        {/* Experiment grid */}
        {!isLoading && !isError && experiments.length > 0 && (
          <AnimatedSection delay={200}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {experiments.map((experiment, index) => (
                <div
                  key={experiment.id}
                  className="transition-all duration-300 ease-out"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <ExperimentCard
                    experiment={experiment}
                    onClick={handleExperimentClick}
                  />
                </div>
              ))}
            </div>
          </AnimatedSection>
        )}
      </main>

      {/* Create Experiment Modal */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[500px] border-slate-200 shadow-xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-900">
              Novo Experimento
            </DialogTitle>
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
