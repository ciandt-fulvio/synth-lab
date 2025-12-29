// frontend/src/components/experiments/results/ExtremeCasesSection.tsx
// Section with extreme cases tables and explanation

import { useState } from 'react';
import { HelpCircle, UserX, UserCheck, HelpCircle as Unexpected } from 'lucide-react';
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
import type { ExtremeSynth } from '@/types/simulation';

interface ExtremeCasesSectionProps {
  experimentId: string;
}

interface SynthCardProps {
  synth: ExtremeSynth;
  variant: 'failure' | 'success' | 'unexpected';
}

function SynthCard({ synth, variant }: SynthCardProps) {
  const variantStyles = {
    failure: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: <UserX className="h-4 w-4 text-red-500" />,
      rateColor: 'text-red-600',
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: <UserCheck className="h-4 w-4 text-green-500" />,
      rateColor: 'text-green-600',
    },
    unexpected: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      icon: <Unexpected className="h-4 w-4 text-amber-500" />,
      rateColor: 'text-amber-600',
    },
  };

  const styles = variantStyles[variant];

  return (
    <div className={`${styles.bg} ${styles.border} border rounded-lg p-3`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {styles.icon}
          <span className="text-xs font-mono text-slate-600 truncate max-w-32">
            {synth.synth_id.substring(0, 12)}...
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
      {synth.interview_questions && synth.interview_questions.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-200">
          <p className="text-xs text-slate-500 mb-1">Perguntas sugeridas:</p>
          <ul className="text-xs text-slate-600 list-disc ml-3 space-y-0.5">
            {synth.interview_questions.slice(0, 2).map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function ExtremeCasesSection({ experimentId }: ExtremeCasesSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const extremeCases = useAnalysisExtremeCases(experimentId, 10);

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
                  os que mais falharam, os que mais tiveram sucesso, e os inesperados (alta capacidade
                  mas baixo sucesso, ou vice-versa).
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Categorias</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong className="text-red-600">Piores Falhas</strong>: Menor taxa de sucesso</li>
                  <li><strong className="text-green-600">Melhores Sucessos</strong>: Maior taxa de sucesso</li>
                  <li><strong className="text-amber-600">Casos Inesperados</strong>: Resultados contrários ao esperado</li>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Worst Failures */}
            <div>
              <h4 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-2">
                <UserX className="h-4 w-4" />
                Piores Falhas ({extremeCases.data.worst_failures.length})
              </h4>
              <div className="space-y-2">
                {extremeCases.data.worst_failures.slice(0, 5).map((synth) => (
                  <SynthCard key={synth.synth_id} synth={synth} variant="failure" />
                ))}
                {extremeCases.data.worst_failures.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Nenhum caso encontrado</p>
                )}
              </div>
            </div>

            {/* Best Successes */}
            <div>
              <h4 className="text-sm font-semibold text-green-700 mb-3 flex items-center gap-2">
                <UserCheck className="h-4 w-4" />
                Melhores Sucessos ({extremeCases.data.best_successes.length})
              </h4>
              <div className="space-y-2">
                {extremeCases.data.best_successes.slice(0, 5).map((synth) => (
                  <SynthCard key={synth.synth_id} synth={synth} variant="success" />
                ))}
                {extremeCases.data.best_successes.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Nenhum caso encontrado</p>
                )}
              </div>
            </div>

            {/* Unexpected Cases */}
            <div>
              <h4 className="text-sm font-semibold text-amber-700 mb-3 flex items-center gap-2">
                <Unexpected className="h-4 w-4" />
                Casos Inesperados ({extremeCases.data.unexpected_cases.length})
              </h4>
              <div className="space-y-2">
                {extremeCases.data.unexpected_cases.slice(0, 5).map((synth) => (
                  <SynthCard key={synth.synth_id} synth={synth} variant="unexpected" />
                ))}
                {extremeCases.data.unexpected_cases.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Nenhum caso encontrado</p>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
