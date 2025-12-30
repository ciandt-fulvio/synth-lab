// frontend/src/components/experiments/results/PDPSection.tsx
// Section with PDP charts and feature selector

import { useState } from 'react';
import { HelpCircle, LineChart as LineChartIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { PDPChart } from './charts/PDPChart';
import { PDPComparisonChart } from './charts/PDPComparisonChart';
import { useAnalysisPDP, useAnalysisPDPComparison } from '@/hooks/use-analysis-charts';

interface PDPSectionProps {
  experimentId: string;
}

const FEATURE_OPTIONS = [
  { value: 'capability_mean', label: 'Capacidade' },
  { value: 'trust_mean', label: 'Confiança' },
  { value: 'friction_tolerance_mean', label: 'Tolerância' },
  { value: 'exploration_prob', label: 'Exploração' },
  { value: 'digital_literacy', label: 'Lit. Digital' },
  { value: 'similar_tool_experience', label: 'Exp. Similar' },
  { value: 'motor_ability', label: 'Hab. Motora' },
  { value: 'time_availability', label: 'Disponibilidade' },
  { value: 'domain_expertise', label: 'Expertise' },
];

const DEFAULT_COMPARISON_FEATURES = ['capability_mean', 'trust_mean', 'friction_tolerance_mean'];

export function PDPSection({ experimentId }: PDPSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState('trust_mean');
  const [viewMode, setViewMode] = useState<'single' | 'comparison'>('single');

  // Single feature PDP
  const pdp = useAnalysisPDP(experimentId, selectedFeature, 20, viewMode === 'single');

  // Comparison PDP
  const pdpComparison = useAnalysisPDPComparison(
    experimentId,
    DEFAULT_COMPARISON_FEATURES,
    20,
    viewMode === 'comparison'
  );

  const currentData = viewMode === 'single' ? pdp : pdpComparison;

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <LineChartIcon className="h-4 w-4 text-slate-500" />
          Dependência Parcial (PDP)
        </CardTitle>
        <p className="text-meta">Como a probabilidade de sucesso varia conforme o valor de cada atributo</p>
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
                  <span className="text-sm font-medium">O que é PDP?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é Dependência Parcial?</h4>
                <p className="text-xs">
                  PDP (Partial Dependence Plot) mostra como a <strong>probabilidade de sucesso</strong>
                  muda quando variamos um atributo específico, mantendo todos os outros constantes.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Eixo X</strong>: Valores do atributo selecionado</li>
                  <li><strong>Eixo Y</strong>: Probabilidade média de sucesso</li>
                  <li><strong>Inclinação</strong>: Direção e força do efeito</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Tipos de Efeito</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Linear</strong>: Efeito constante - cada unidade adicional tem o mesmo impacto</li>
                  <li><strong>Monotônico</strong>: Sempre aumenta ou sempre diminui</li>
                  <li><strong>Não Linear</strong>: O efeito varia dependendo do valor</li>
                  <li><strong>Threshold</strong>: Existe um "ponto de virada" importante</li>
                </ul>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Controls */}
        <div className="bg-slate-50 rounded-lg p-4 space-y-4">
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'single' | 'comparison')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="single">Feature Única</TabsTrigger>
              <TabsTrigger value="comparison">Comparação</TabsTrigger>
            </TabsList>

            <TabsContent value="single" className="pt-4">
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-600">Atributo:</span>
                <Select value={selectedFeature} onValueChange={setSelectedFeature}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FEATURE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>

            <TabsContent value="comparison" className="pt-4">
              <p className="text-sm text-slate-600">
                Comparando: {DEFAULT_COMPARISON_FEATURES.map((f) =>
                  FEATURE_OPTIONS.find((o) => o.value === f)?.label || f
                ).join(', ')}
              </p>
            </TabsContent>
          </Tabs>
        </div>

        {/* Loading state */}
        {currentData.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 350 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {/* Error state */}
        {currentData.isError && !currentData.isLoading && (
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
              onClick={() => currentData.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!currentData.data && !currentData.isLoading && !currentData.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <LineChartIcon className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {/* Chart - Single Feature */}
        {viewMode === 'single' && !pdp.isLoading && !pdp.isError && pdp.data && (
          <div style={{ minHeight: 350 }}>
            <ChartErrorBoundary chartName="PDP">
              <PDPChart data={pdp.data} />
            </ChartErrorBoundary>
          </div>
        )}

        {/* Chart - Comparison */}
        {viewMode === 'comparison' && !pdpComparison.isLoading && !pdpComparison.isError && pdpComparison.data && (
          <div style={{ minHeight: 400 }}>
            <ChartErrorBoundary chartName="PDP Comparison">
              <PDPComparisonChart data={pdpComparison.data} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
