/**
 * T024 Index page - Experiment List (Home).
 *
 * Main page showing grid of experiment cards.
 * Research Observatory aesthetic with animated elements.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US1)
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ExperimentCard } from '@/components/experiments/ExperimentCard';
import { EmptyState } from '@/components/experiments/EmptyState';
import { ExperimentForm } from '@/components/experiments/ExperimentForm';
import { ExperimentsFilter, type SortOption } from '@/components/experiments/ExperimentsFilter';
import { PopularTags } from '@/components/experiments/PopularTags';
import { useExperiments, useCreateExperiment } from '@/hooks/use-experiments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plus, Users, FlaskConical, Sparkles, Search, Loader2 } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentCreate } from '@/types/experiment';
import type { ExperimentsListParams } from '@/services/experiments-api';

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

  // Search, tag filter, and sort state
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [sortOption, setSortOption] = useState<SortOption>('recent');

  // Convert UI state to API params
  const listParams = useMemo<ExperimentsListParams>(() => ({
    search: search || undefined, // Don't send empty string
    tag: selectedTag || undefined,
    sort_by: sortOption === 'name' ? 'name' : 'created_at',
    sort_order: sortOption === 'name' ? 'asc' : 'desc',
  }), [search, selectedTag, sortOption]);

  // Fetch experiments with params
  const { data, isLoading, isError, error, isFetching } = useExperiments(listParams);
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

  const handleTagClick = (tag: string | null) => {
    setSelectedTag(tag);
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

        {/* Popular Tags Quick Filters */}
        {!isLoading && !isError && experiments.length > 0 && (
          <AnimatedSection delay={50}>
            <PopularTags
              selectedTag={selectedTag}
              onTagClick={handleTagClick}
            />
          </AnimatedSection>
        )}

        {/* Search and Sort Controls */}
        {!isLoading && !isError && (
          <AnimatedSection delay={100}>
            <ExperimentsFilter
              search={search}
              sortOption={sortOption}
              selectedTag={selectedTag}
              onSearchChange={setSearch}
              onSortChange={setSortOption}
              onTagChange={setSelectedTag}
            />
          </AnimatedSection>
        )}

        {/* Loading indicator during fetch (not initial load) */}
        {isFetching && !isLoading && (
          <div className="flex justify-center py-2 mb-4">
            <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
          </div>
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

        {/* Empty state - different message when searching */}
        {!isLoading && !isError && experiments.length === 0 && (
          <AnimatedSection delay={0}>
            {search || selectedTag ? (
              <div className="text-center py-12">
                <Search className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  Nenhum experimento encontrado
                </h3>
                <p className="text-slate-500">
                  Nenhum resultado para {search && `"${search}"`}{search && selectedTag && ' e '}{selectedTag && `"${selectedTag}"`}
                </p>
              </div>
            ) : (
              <EmptyState onCreateClick={handleCreateClick} />
            )}
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
