// frontend/src/components/experiments/results/ExtremeCasesSection.tsx
// Section with extreme cases tables and explanation

import { useState } from 'react';
import { HelpCircle, UserX, UserCheck, Loader2, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw, Users } from 'lucide-react';
import { useAnalysisExtremeCases } from '@/hooks/use-analysis-charts';
import { useAutoInterview, useCreateAutoInterview } from '@/hooks/use-experiments';
import { toast } from 'sonner';
import type { ExtremeSynth } from '@/types/simulation';

import { InsightSection } from './InsightSection';
interface ExtremeCasesSectionProps {
  experimentId: string;
  onSynthClick?: (synthId: string) => void;
  selectedSynthId?: string | null;
}

interface SynthCardProps {
  synth: ExtremeSynth;
  variant: 'failure' | 'success';
  onClick?: () => void;
  isSelected?: boolean;
}

function SynthCard({ synth, variant, onClick, isSelected }: SynthCardProps) {
  const variantStyles = {
    failure: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      hover: 'hover:bg-red-100 hover:border-red-300',
      selected: 'ring-2 ring-red-400 bg-red-100',
      icon: <UserX className="h-4 w-4 text-red-500" />,
      rateColor: 'text-red-600',
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      hover: 'hover:bg-green-100 hover:border-green-300',
      selected: 'ring-2 ring-green-400 bg-green-100',
      icon: <UserCheck className="h-4 w-4 text-green-500" />,
      rateColor: 'text-green-600',
    },
  };

  const styles = variantStyles[variant];

  return (
    <button
      onClick={onClick}
      className={`${styles.bg} ${styles.border} border rounded-lg p-3 w-full text-left transition-all cursor-pointer ${styles.hover} ${
        isSelected ? styles.selected : ''
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            {styles.icon}
            <span className="text-sm font-medium text-slate-800 truncate max-w-40">
              {synth.synth_name || synth.synth_id.substring(0, 8)}
            </span>
          </div>
          <span className="text-xs font-mono text-slate-400 truncate max-w-40 ml-6">
            {synth.synth_id}
          </span>
        </div>
        <span className={`text-sm font-bold ${styles.rateColor}`}>
          {(synth.success_rate * 100).toFixed(0)}%
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <span className="text-slate-500">Sucesso</span>
          <p className="font-medium text-green-600">{(synth.success_rate * 100).toFixed(0)}%</p>
        </div>
        <div>
          <span className="text-slate-500">Falha</span>
          <p className="font-medium text-red-600">{(synth.failed_rate * 100).toFixed(0)}%</p>
        </div>
        <div>
          <span className="text-slate-500">Não Tentou</span>
          <p className="font-medium text-slate-600">{(synth.did_not_try_rate * 100).toFixed(0)}%</p>
        </div>
      </div>
    </button>
  );
}

export function ExtremeCasesSection({
  experimentId,
  onSynthClick,
  selectedSynthId,
}: ExtremeCasesSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const extremeCases = useAnalysisExtremeCases(experimentId, 10);
  const autoInterview = useAutoInterview(experimentId);
  const createAutoInterview = useCreateAutoInterview();

  const handleCreateInterview = () => {
    createAutoInterview.mutate(experimentId, {
      onSuccess: () => {
        toast.success('Entrevista criada com sucesso', {
          description: '10 casos extremos selecionados (5 melhores + 5 piores)',
        });
      },
      onError: (error) => {
        const errorMessage = error instanceof Error ? error.message : 'Erro ao criar entrevista';
        toast.error('Falha ao criar entrevista', {
          description: errorMessage,
        });
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-500" />
          Casos Extremos
        </CardTitle>
        <p className="text-meta">Synths com resultados mais extremos para seleção de entrevistas</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Explanation section - collapsible */}
        <Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
          <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
              >
                <div className="flex items-center gap-2 text-indigo-700">
                  <HelpCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Como usar estes casos?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que são casos extremos?</h4>
                <p className="text-xs">
                  Casos extremos são synths com resultados nos <strong>extremos da distribuição</strong>:
                  os que mais falharam (bottom 5) e os que mais tiveram sucesso (top 5).
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Categorias</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong className="text-red-600">Piores Falhas</strong>: Menor taxa de sucesso (bottom 5)</li>
                  <li><strong className="text-green-600">Melhores Sucessos</strong>: Maior taxa de sucesso (top 5)</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que entrevistar?</h4>
                <p className="text-xs">
                  Entrevistas qualitativas com estes synths revelam <strong>insights profundos</strong>
                  sobre o que causa sucesso ou falha que os dados quantitativos não mostram.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading state */}
        {extremeCases.isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {extremeCases.isError && !extremeCases.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">Erro ao carregar os dados. Tente novamente.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => extremeCases.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!extremeCases.data && !extremeCases.isLoading && !extremeCases.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <Users className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum caso extremo encontrado.</p>
            </div>
          </div>
        )}

        {/* Data display */}
        {!extremeCases.isLoading && !extremeCases.isError && extremeCases.data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Bottom 5 Performers */}
            <div>
              <h4 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-2">
                <UserX className="h-4 w-4" />
                Piores Falhas ({extremeCases.data.worst_failures.length})
              </h4>
              <div className="space-y-2">
                {extremeCases.data.worst_failures.slice(0, 5).map((synth) => (
                  <SynthCard
                    key={synth.synth_id}
                    synth={synth}
                    variant="failure"
                    onClick={() => onSynthClick?.(synth.synth_id)}
                    isSelected={selectedSynthId === synth.synth_id}
                  />
                ))}
                {extremeCases.data.worst_failures.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Nenhum caso encontrado</p>
                )}
              </div>
            </div>

            {/* Top 5 Performers */}
            <div>
              <h4 className="text-sm font-semibold text-green-700 mb-3 flex items-center gap-2">
                <UserCheck className="h-4 w-4" />
                Melhores Sucessos ({extremeCases.data.best_successes.length})
              </h4>
              <div className="space-y-2">
                {extremeCases.data.best_successes.slice(0, 5).map((synth) => (
                  <SynthCard
                    key={synth.synth_id}
                    synth={synth}
                    variant="success"
                    onClick={() => onSynthClick?.(synth.synth_id)}
                    isSelected={selectedSynthId === synth.synth_id}
                  />
                ))}
                {extremeCases.data.best_successes.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Nenhum caso encontrado</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Auto-Interview Button */}
        {!extremeCases.isLoading && !extremeCases.isError && extremeCases.data && (
          <div className="mt-6 pt-4 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-1">Entrevista Automática</h4>
                <p className="text-xs text-slate-500">
                  {autoInterview.data
                    ? 'Entrevista criada com os 10 casos mais extremos'
                    : 'Crie uma entrevista com os 10 casos mais extremos (5 melhores + 5 piores)'}
                </p>
              </div>

              {autoInterview.data ? (
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  className="btn-secondary"
                >
                  <a href={`/interviews/${autoInterview.data.exec_id}`}>
                    <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                    Ver Entrevista
                  </a>
                </Button>
              ) : (
                <Button
                  onClick={handleCreateInterview}
                  disabled={createAutoInterview.isPending}
                  size="sm"
                  className="btn-primary"
                >
                  {createAutoInterview.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                      Criando...
                    </>
                  ) : (
                    <>
                      <Users className="h-3.5 w-3.5 mr-1.5" />
                      Criar Entrevista
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        )}
        {/* AI-Generated Insights */}
        <InsightSection experimentId={experimentId} chartType="extreme_cases" />

    </Card>
  );
}
