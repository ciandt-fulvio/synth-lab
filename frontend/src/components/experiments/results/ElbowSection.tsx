// frontend/src/components/experiments/results/ElbowSection.tsx
// Section with Elbow chart for K-Means clustering and explanation

import { useState } from 'react';
import { HelpCircle, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { ElbowChart } from './charts/ElbowChart';
import { useAnalysisElbow } from '@/hooks/use-analysis-charts';

interface ElbowSectionProps {
  experimentId: string;
  suggestedK?: number;
  onSelectK?: (k: number) => void;
}

export function ElbowSection({ experimentId, suggestedK = 3, onSelectK }: ElbowSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const elbow = useAnalysisElbow(experimentId);

  const handleGenerateInsight = () => {
    if (!elbow.data) return;
    generateInsight.mutate({
      chartType: 'elbow',
      chartData: {
        points: elbow.data,
        suggested_k: suggestedK,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <TrendingDown className="h-4 w-4 text-slate-500" />
          Método Elbow
        </CardTitle>
        <p className="text-meta">Determina o número ideal de clusters observando onde a curva "dobra"</p>
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
                  <span className="text-sm font-medium">Como interpretar este gráfico?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é o Método Elbow?</h4>
                <p className="text-xs">
                  O método Elbow ajuda a escolher o número ideal de clusters (K). A <strong>inércia</strong>
                  {' '}mede quão próximos os pontos estão do centro de seus clusters. Quanto menor, melhor.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como encontrar o "cotovelo"?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li>A curva cai rapidamente no início</li>
                  <li>Em algum ponto, ela começa a cair mais lentamente</li>
                  <li>O <strong>"cotovelo"</strong> é onde essa transição acontece</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que isso importa?</h4>
                <p className="text-xs">
                  Adicionar mais clusters sempre reduz a inércia, mas a partir do cotovelo,
                  o ganho é marginal. O K do cotovelo oferece o melhor equilíbrio entre
                  <strong> simplicidade</strong> e <strong>qualidade</strong>.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Chart area with loading/error/empty states */}
        {elbow.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 350 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {elbow.isError && !elbow.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
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
              onClick={() => elbow.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {(!elbow.data || elbow.data.length === 0) && !elbow.isLoading && !elbow.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <TrendingDown className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {!elbow.isLoading && !elbow.isError && elbow.data && elbow.data.length > 0 && (
          <div style={{ minHeight: 350 }}>
            <ChartErrorBoundary chartName="Elbow">
              <ElbowChart
                data={elbow.data}
                suggestedK={suggestedK}
                onSelectK={onSelectK}
              />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
