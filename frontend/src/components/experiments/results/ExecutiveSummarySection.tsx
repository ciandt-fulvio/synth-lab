// frontend/src/components/experiments/results/ExecutiveSummarySection.tsx
// Section displaying executive summary with markdown rendering

import { useState } from 'react';
import { HelpCircle, FileText, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAnalysisInsights, useGenerateAnalysisExecutiveSummary } from '@/hooks/use-insights';

interface ExecutiveSummarySectionProps {
  experimentId: string;
}

export function ExecutiveSummarySection({ experimentId }: ExecutiveSummarySectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const insights = useAnalysisInsights(experimentId);
  const generateSummary = useGenerateAnalysisExecutiveSummary(experimentId);

  const hasSummary = !!insights.data?.executive_summary;
  const hasInsights = insights.data?.insights && insights.data.insights.length > 0;

  const handleGenerateSummary = () => {
    generateSummary.mutate();
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-card-title flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-500" />
              Resumo Executivo
            </CardTitle>
            <p className="text-meta">Síntese consolidada de todos os insights para stakeholders</p>
          </div>
          {hasInsights && (
            <Button
              onClick={handleGenerateSummary}
              disabled={generateSummary.isPending}
              className="btn-primary"
              size="sm"
            >
              {generateSummary.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              {hasSummary ? 'Regenerar' : 'Gerar'} Resumo
            </Button>
          )}
        </div>
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
                  <span className="text-sm font-medium">O que é o Resumo Executivo?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Para que serve?</h4>
                <p className="text-xs">
                  O Resumo Executivo <strong>consolida todos os insights</strong> em um documento
                  único e conciso, ideal para apresentar a stakeholders e tomadores de decisão.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que contém?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Principais Descobertas</strong>: Padrões e problemas identificados</li>
                  <li><strong>Métricas Chave</strong>: Números que suportam as conclusões</li>
                  <li><strong>Recomendações</strong>: Ações prioritárias sugeridas</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Pré-requisitos</h4>
                <p className="text-xs">
                  O resumo é gerado a partir dos <strong>insights existentes</strong>. Gere insights
                  nos gráficos antes de solicitar o resumo executivo.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading state */}
        {(insights.isLoading || generateSummary.isPending) && (
          <div className="space-y-3">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-8 w-48 mt-4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        )}

        {/* Error state */}
        {(insights.isError || generateSummary.isError) && !insights.isLoading && !generateSummary.isPending && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">Erro ao carregar ou gerar o resumo. Tente novamente.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => insights.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state - no insights */}
        {!hasInsights && !hasSummary && !insights.isLoading && !insights.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <FileText className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Insights</p>
              <p className="text-meta">
                Gere insights nos gráficos antes de criar o resumo executivo.
              </p>
            </div>
          </div>
        )}

        {/* Empty state - has insights but no summary */}
        {hasInsights && !hasSummary && !insights.isLoading && !insights.isError && !generateSummary.isPending && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <FileText className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Resumo Não Gerado</p>
              <p className="text-meta">
                Você tem {insights.data!.insights.length} insight(s). Clique em "Gerar Resumo"
                para criar o resumo executivo consolidado.
              </p>
            </div>
          </div>
        )}

        {/* Summary content */}
        {hasSummary && !insights.isLoading && !generateSummary.isPending && (
          <div className="prose prose-sm prose-slate max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {insights.data!.executive_summary!}
            </ReactMarkdown>
          </div>
        )}

        {/* Last updated */}
        {hasSummary && insights.data?.updated_at && (
          <div className="text-xs text-slate-400 text-right">
            Atualizado em: {new Date(insights.data.updated_at).toLocaleString('pt-BR')}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
