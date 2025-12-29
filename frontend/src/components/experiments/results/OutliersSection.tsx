// frontend/src/components/experiments/results/OutliersSection.tsx
// Section with outliers table, contamination slider, and explanation

import { useState } from 'react';
import { HelpCircle, AlertTriangle, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useAnalysisOutliers } from '@/hooks/use-analysis-charts';
import type { OutlierSynth } from '@/types/simulation';

interface OutliersSectionProps {
  experimentId: string;
  onSynthClick?: (synthId: string) => void;
  selectedSynthId?: string | null;
}

interface OutlierCardProps {
  outlier: OutlierSynth;
  onClick?: () => void;
  isSelected?: boolean;
}

function OutlierCard({ outlier, onClick, isSelected }: OutlierCardProps) {
  return (
    <button
      onClick={onClick}
      className={`bg-amber-50 border border-amber-200 rounded-lg p-3 w-full text-left transition-all cursor-pointer hover:bg-amber-100 hover:border-amber-300 ${
        isSelected ? 'ring-2 ring-amber-400 bg-amber-100' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span className="text-xs font-mono text-slate-600 truncate max-w-32">
            {outlier.synth_id.substring(0, 12)}...
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs mb-2">
        <div>
          <span className="text-slate-500">Sucesso</span>
          <p className="font-medium text-green-600">{(outlier.success_rate * 100).toFixed(0)}%</p>
        </div>
        <div>
          <span className="text-slate-500">Falha</span>
          <p className="font-medium text-red-600">{(outlier.failed_rate * 100).toFixed(0)}%</p>
        </div>
        <div>
          <span className="text-slate-500">Não Tentou</span>
          <p className="font-medium text-slate-600">{(outlier.did_not_try_rate * 100).toFixed(0)}%</p>
        </div>
      </div>

      <p className="text-xs text-slate-600 italic">
        {outlier.explanation}
      </p>
    </button>
  );
}

export function OutliersSection({ experimentId, onSynthClick, selectedSynthId }: OutliersSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [contamination, setContamination] = useState(0.1);

  const outliers = useAnalysisOutliers(experimentId, contamination);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Search className="h-4 w-4 text-slate-500" />
          Outliers Estatísticos
        </CardTitle>
        <p className="text-meta">Synths com padrões estatisticamente anômalos detectados por Isolation Forest</p>
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
                  <span className="text-sm font-medium">O que são outliers?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é um outlier?</h4>
                <p className="text-xs">
                  Outliers são synths com <strong>padrões incomuns</strong> - combinações de atributos
                  ou resultados que diferem significativamente da maioria dos synths.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Tipos de Outliers</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Atributo</strong>: Combinação rara de atributos</li>
                  <li><strong>Resultado</strong>: Resultado inesperado para seus atributos</li>
                  <li><strong>Ambos</strong>: Atributos E resultados anômalos</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Contaminação</h4>
                <p className="text-xs">
                  O slider controla a <strong>sensibilidade</strong>. Valores maiores encontram mais
                  outliers (incluindo casos menos extremos). Comece com 10% e ajuste conforme necessário.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Sensitivity slider */}
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-600">Sensibilidade de Detecção</span>
            <span className="text-sm font-medium text-slate-800">{(contamination * 100).toFixed(0)}%</span>
          </div>
          <Slider
            value={[contamination * 100]}
            onValueChange={([value]) => setContamination(value / 100)}
            min={1}
            max={30}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>Menos outliers</span>
            <span>Mais outliers</span>
          </div>
        </div>

        {/* Stats summary */}
        {outliers.data && (
          <div className="flex items-center justify-center gap-6 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-700">{outliers.data.outliers.length}</p>
              <p className="text-xs text-amber-600">Outliers encontrados</p>
            </div>
            <div className="h-8 w-px bg-amber-200" />
            <div className="text-center">
              <p className="text-2xl font-bold text-slate-700">{outliers.data.total_synths}</p>
              <p className="text-xs text-slate-500">Total de synths</p>
            </div>
            <div className="h-8 w-px bg-amber-200" />
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-700">{outliers.data.outlier_percentage.toFixed(1)}%</p>
              <p className="text-xs text-amber-600">Porcentagem</p>
            </div>
          </div>
        )}

        {/* Loading state */}
        {outliers.isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        )}

        {/* Error state */}
        {outliers.isError && !outliers.isLoading && (
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
              onClick={() => outliers.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state */}
        {outliers.data && outliers.data.outliers.length === 0 && !outliers.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ minHeight: 200 }}
          >
            <div className="icon-box-neutral">
              <Search className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Nenhum Outlier</p>
              <p className="text-meta">Aumente a sensibilidade para encontrar mais outliers.</p>
            </div>
          </div>
        )}

        {/* Data display */}
        {!outliers.isLoading && !outliers.isError && outliers.data && outliers.data.outliers.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {outliers.data.outliers.map((outlier) => (
              <OutlierCard
                key={outlier.synth_id}
                outlier={outlier}
                onClick={() => onSynthClick?.(outlier.synth_id)}
                isSelected={selectedSynthId === outlier.synth_id}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
