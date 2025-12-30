/**
 * InsightSection Component
 *
 * Displays AI-generated insights within individual chart cards.
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 1)
 *   - Hook: src/hooks/use-chart-insight.ts
 *
 * Features:
 *   - Collapsed by default (collapsible UI)
 *   - Loading state with spinner
 *   - Error/failed states with alerts
 *   - Completed state with summary text
 *   - Metadata footer with model and timestamp
 */

import { useState } from 'react';
import { Sparkles, Loader2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useChartInsight } from '@/hooks/use-chart-insight';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface InsightSectionProps {
  experimentId: string;
  chartType: string;
}

export function InsightSection({ experimentId, chartType }: InsightSectionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: insight, isLoading, error } = useChartInsight(experimentId, chartType);

  // Don't render if no insight available yet (404 error on first fetch)
  if (error && error.message?.includes('404')) {
    return null;
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-6">
      <div className="border border-indigo-100 bg-gradient-to-r from-indigo-50 to-violet-50 rounded-lg">
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-between p-4 hover:bg-indigo-100/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              <span className="font-medium text-indigo-900">Insights de IA</span>
              {insight?.status === 'pending' && (
                <Badge variant="outline" className="ml-2 border-amber-300 bg-amber-50 text-amber-800">
                  Gerando...
                </Badge>
              )}
              {insight?.status === 'completed' && (
                <Badge variant="outline" className="ml-2 border-green-300 bg-green-50 text-green-800">
                  Pronto
                </Badge>
              )}
              {insight?.status === 'failed' && (
                <Badge variant="outline" className="ml-2 border-red-300 bg-red-50 text-red-800">
                  Falhou
                </Badge>
              )}
            </div>
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4">
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
                <span className="ml-2 text-sm text-slate-600">Carregando insights...</span>
              </div>
            )}

            {/* Error State (non-404) */}
            {error && !error.message?.includes('404') && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Erro ao carregar insights. Tente novamente mais tarde.
                </AlertDescription>
              </Alert>
            )}

            {/* Failed State */}
            {insight?.status === 'failed' && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Não foi possível gerar insights para este gráfico.
                </AlertDescription>
              </Alert>
            )}

            {/* Pending State */}
            {insight?.status === 'pending' && (
              <div className="space-y-3 mt-4">
                <div className="flex items-center gap-2 text-amber-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Gerando insights...</span>
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            )}

            {/* Completed State - Simplified to just summary */}
            {insight?.status === 'completed' && (
              <div className="space-y-4 mt-4">
                {/* Summary */}
                <p className="text-sm text-slate-700 leading-relaxed">
                  {insight.summary}
                </p>

                {/* Metadata Footer */}
                <div className="pt-3 border-t border-indigo-100 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>Modelo: {insight.model}</span>
                  </div>
                  <span>
                    Gerado{' '}
                    {formatDistanceToNow(new Date(insight.generation_timestamp), {
                      addSuffix: true,
                      locale: ptBR,
                    })}
                  </span>
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
