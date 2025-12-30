/**
 * ExecutiveSummaryModal Component
 *
 * Side panel (Sheet) displaying executive summary synthesizing all chart insights.
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2)
 *   - Hook: src/hooks/use-executive-summary.ts
 *
 * Features:
 *   - Right-side sheet layout
 *   - Loading state (spinner + message)
 *   - Partial summary state (warning alert with chart count)
 *   - Completed state with 4 sections + recommendations
 *   - Metadata footer
 */

import { Loader2, Sparkles, AlertCircle, CheckCircle2, TrendingUp, Users, AlertTriangle, Lightbulb } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useExecutiveSummary } from '@/hooks/use-executive-summary';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface ExecutiveSummaryModalProps {
  experimentId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExecutiveSummaryModal({
  experimentId,
  isOpen,
  onClose,
}: ExecutiveSummaryModalProps) {
  const { data: summary, isLoading, error } = useExecutiveSummary(experimentId, {
    enabled: isOpen,
  });

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-600" />
            Resumo Executivo
          </SheetTitle>
          <SheetDescription>
            Síntese de todos os insights gerados pela análise quantitativa
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-4" />
              <p className="text-sm text-slate-600">Gerando resumo executivo...</p>
              <p className="text-xs text-slate-500 mt-1">
                Aguarde enquanto sintetizamos todos os insights
              </p>
            </div>
          )}

          {/* Error State (non-404) */}
          {error && !error.message?.includes('404') && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Erro ao carregar resumo executivo. Tente novamente mais tarde.
              </AlertDescription>
            </Alert>
          )}

          {/* 404 State - Summary not generated yet */}
          {error && error.message?.includes('404') && (
            <Alert className="border-amber-200 bg-amber-50">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800">
                Resumo executivo ainda não foi gerado. Execute uma análise para gerar insights.
              </AlertDescription>
            </Alert>
          )}

          {/* Partial Summary Warning */}
          {summary?.status === 'partial' && (
            <Alert className="border-amber-200 bg-amber-50">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800">
                <strong>Resumo Parcial:</strong> Gerado com base em{' '}
                {summary.included_chart_types.length} de 7 gráficos. Alguns insights podem estar
                pendentes.
              </AlertDescription>
            </Alert>
          )}

          {/* Pending State */}
          {summary?.status === 'pending' && (
            <div className="space-y-4">
              <Alert className="border-indigo-200 bg-indigo-50">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                <AlertDescription className="text-indigo-800">
                  Resumo executivo está sendo gerado... Recarregando automaticamente.
                </AlertDescription>
              </Alert>
              <div className="space-y-3">
                <div className="h-4 w-full bg-slate-200 rounded animate-pulse" />
                <div className="h-4 w-3/4 bg-slate-200 rounded animate-pulse" />
                <div className="h-4 w-5/6 bg-slate-200 rounded animate-pulse" />
              </div>
            </div>
          )}

          {/* Failed State */}
          {summary?.status === 'failed' && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Falha ao gerar resumo executivo. Por favor, tente executar a análise novamente.
              </AlertDescription>
            </Alert>
          )}

          {/* Completed State */}
          {(summary?.status === 'completed' || summary?.status === 'partial') && (
            <div className="space-y-6">
              {/* Overview Section */}
              <div className="border-l-4 border-indigo-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-indigo-600" />
                  <h3 className="text-base font-semibold text-slate-900">Visão Geral</h3>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{summary.overview}</p>
              </div>

              {/* Explainability Section */}
              <div className="border-l-4 border-green-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="h-4 w-4 text-green-600" />
                  <h3 className="text-base font-semibold text-slate-900">Explicabilidade</h3>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{summary.explainability}</p>
              </div>

              {/* Segmentation Section */}
              <div className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-4 w-4 text-blue-600" />
                  <h3 className="text-base font-semibold text-slate-900">Segmentação</h3>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{summary.segmentation}</p>
              </div>

              {/* Edge Cases Section */}
              <div className="border-l-4 border-amber-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  <h3 className="text-base font-semibold text-slate-900">Casos Extremos</h3>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{summary.edge_cases}</p>
              </div>

              {/* Recommendations Section */}
              <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="h-5 w-5 text-violet-600" />
                  <h3 className="text-base font-semibold text-violet-900">Recomendações</h3>
                </div>
                <ol className="space-y-2">
                  {summary.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <Badge className="badge-primary shrink-0 mt-0.5">{idx + 1}</Badge>
                      <span className="text-sm text-slate-800 leading-relaxed">{rec}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Metadata Footer */}
              <div className="border-t border-slate-200 pt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                <div className="flex items-center gap-4">
                  <span>Modelo: {summary.model}</span>
                  <span>
                    {summary.included_chart_types.length} de 7 gráficos analisados
                  </span>
                </div>
                <span>
                  Gerado{' '}
                  {formatDistanceToNow(new Date(summary.generation_timestamp), {
                    addSuffix: true,
                    locale: ptBR,
                  })}
                </span>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
