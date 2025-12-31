// frontend/src/components/experiments/results/SankeyFlowSection.tsx
// Section with Sankey Flow chart showing outcome flow visualization

import { GitBranch, HelpCircle } from 'lucide-react';
import { useState } from 'react';
import { SankeyFlowChart } from './charts/SankeyFlowChart';
import { useAnalysisSankeyFlow } from '@/hooks/use-analysis-charts';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';

interface SankeyFlowSectionProps {
  experimentId: string;
}

export function SankeyFlowSection({ experimentId }: SankeyFlowSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const { data, isLoading, error, refetch, isRefetching } = useAnalysisSankeyFlow(experimentId);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-slate-500" />
          Fluxo de Resultados
        </CardTitle>
        <p className="text-meta">
          Visualização do fluxo de synths desde a população até os outcomes e causas raiz
        </p>
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
                  <span className="text-sm font-medium">Como interpretar este diagrama?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-3 text-sm text-slate-600 space-y-2">
              <p>
                O diagrama Sankey mostra como os synths fluem através dos resultados da simulação:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>Nível 1 (População):</strong> Total de synths simulados
                </li>
                <li>
                  <strong>Nível 2 (Outcomes):</strong> Como os synths se distribuem entre
                  "Não tentou" (âmbar), "Falhou" (vermelho) e "Sucesso" (verde)
                </li>
                <li>
                  <strong>Nível 3 (Causas Raiz):</strong> Para synths que não tentaram ou falharam,
                  indica a principal barreira identificada
                </li>
              </ul>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Chart area */}
        <ChartErrorBoundary>
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-[350px] w-full" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <AlertCircle className="h-8 w-8 mb-2 text-red-400" />
              <p className="text-sm mb-2">Erro ao carregar dados do Sankey</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isRefetching}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isRefetching ? 'animate-spin' : ''}`} />
                Tentar novamente
              </Button>
            </div>
          ) : data ? (
            <SankeyFlowChart data={data} />
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-500">
              <p className="text-sm">Nenhum dado disponível</p>
            </div>
          )}
        </ChartErrorBoundary>
      </CardContent>
    </Card>
  );
}
