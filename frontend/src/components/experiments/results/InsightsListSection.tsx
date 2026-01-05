// frontend/src/components/experiments/results/InsightsListSection.tsx
// Section displaying LLM-generated insights with generate buttons

import { useState } from 'react';
import { HelpCircle, Lightbulb, Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useAnalysisInsights } from '@/hooks/use-insights';
import type { ChartInsight } from '@/types/simulation';

interface InsightsListSectionProps {
  experimentId: string;
}

const CHART_TYPE_LABELS: Record<string, string> = {
  try_vs_success: 'Tentativa vs Sucesso',
  outcome_distribution: 'Distribuição de Resultados',
  failure_heatmap: 'Mapa de Calor de Falhas',
  box_plot: 'Box Plot',
  scatter: 'Correlação',
  elbow: 'Método Elbow',
  radar: 'Perfis de Clusters',
  shap_summary: 'SHAP Summary',
  shap_waterfall: 'SHAP Waterfall',
  pdp: 'Dependência Parcial',
};

interface InsightCardProps {
  insight: ChartInsight;
}

function InsightCard({ insight }: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const chartLabel = CHART_TYPE_LABELS[insight.chart_type] || insight.chart_type;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
            <Lightbulb className="h-4 w-4 text-indigo-600" />
          </div>
          <div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
              {chartLabel}
            </span>
          </div>
        </div>
        <span className="text-xs text-slate-400">
          {new Date(insight.generated_at).toLocaleDateString('pt-BR')}
        </span>
      </div>

      {/* Caption */}
      <h4 className="font-semibold text-slate-800 mb-1">{insight.caption.short}</h4>
      <p className="text-sm text-slate-600 mb-3">{insight.caption.medium}</p>

      {/* Expandable content */}
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full text-slate-500 hover:text-slate-700">
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Menos detalhes
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Mais detalhes
              </>
            )}
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="mt-3 space-y-3">
          {/* Explanation */}
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase mb-1">Explicação</h5>
            <p className="text-sm text-slate-600">{insight.explanation}</p>
          </div>

          {/* Evidence */}
          {insight.evidence && insight.evidence.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-1">Evidências</h5>
              <div className="space-y-1">
                {insight.evidence.map((e, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="text-slate-500">{e.metric}:</span>
                    <span className="font-medium text-slate-700">
                      {typeof e.value === 'number' ? (e.value * 100).toFixed(1) + '%' : e.value}
                    </span>
                    <span className="text-xs text-slate-400">({e.interpretation})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendation */}
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <h5 className="text-xs font-semibold text-green-700 uppercase mb-1">Recomendação</h5>
            <p className="text-sm text-green-800">{insight.recommendation}</p>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

export function InsightsListSection({ experimentId }: InsightsListSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const insights = useAnalysisInsights(experimentId);

  const hasInsights = insights.data?.insights && insights.data.insights.length > 0;

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-slate-500" />
          Insights Gerados por IA
        </CardTitle>
        <p className="text-meta">Análises automáticas dos gráficos geradas por LLM</p>
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
                  <span className="text-sm font-medium">O que são estes insights?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Insights Automáticos</h4>
                <p className="text-xs">
                  Insights são <strong>análises geradas por IA</strong> (LLM) a partir dos dados
                  dos gráficos. Eles interpretam padrões, identificam problemas e sugerem ações.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como usar?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li>Revise os insights para entender os dados rapidamente</li>
                  <li>Use as evidências para validar as conclusões</li>
                  <li>Implemente as recomendações prioritárias</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Limitações</h4>
                <p className="text-xs">
                  Insights são <strong>sugestões</strong>, não verdades absolutas. Sempre valide
                  com seu conhecimento do contexto e dos usuários reais.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading state */}
        {insights.isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        )}

        {/* Error state */}
        {insights.isError && !insights.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">Erro ao carregar os insights. Tente novamente.</p>
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

        {/* Empty state */}
        {!hasInsights && !insights.isLoading && !insights.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <Lightbulb className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Insights</p>
              <p className="text-meta">
                Nenhum insight foi gerado ainda. Execute a análise para gerar insights automáticos.
              </p>
            </div>
          </div>
        )}

        {/* Insights list */}
        {hasInsights && !insights.isLoading && !insights.isError && (
          <div className="space-y-3">
            {insights.data!.insights.map((insight, index) => (
              <InsightCard key={`${insight.chart_type}-${index}`} insight={insight} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
