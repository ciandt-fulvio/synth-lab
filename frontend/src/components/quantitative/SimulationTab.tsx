/**
 * SimulationTab container component.
 *
 * Displays simulation results and provides manual interview guide generation.
 * Shows simulation summary button with loading/view states based on document availability.
 *
 * References:
 *   - Hooks: src/hooks/use-quantitative-analysis.ts
 *   - Hooks: src/hooks/use-documents.ts
 *   - Components: SimulationResults, DocumentViewer
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Activity, FileText, BarChart3 } from 'lucide-react';
import {
  useSimulationResults,
} from '@/hooks/use-quantitative-analysis';
import { useDocumentAvailability, useDocumentMarkdown } from '@/hooks/use-documents';
import { DocumentViewer } from '@/components/shared/DocumentViewer';
import { SimulationResults } from './SimulationResults';

interface SimulationTabProps {
  experimentId: string;
  onGenerateGuide?: () => void;
}

export function SimulationTab({ experimentId, onGenerateGuide }: SimulationTabProps) {
  const { data: simulationRun, isLoading } = useSimulationResults(experimentId);
  const { data: availability } = useDocumentAvailability(experimentId);
  const [showViewer, setShowViewer] = useState(false);

  const summaryStatus = availability?.simulation_summary?.status ?? null;
  const isCompleted = summaryStatus === 'completed';
  const isGenerating = summaryStatus === 'generating';

  // Fetch markdown only when viewer is open and document is completed
  const { data: markdownContent, isLoading: isLoadingMarkdown } = useDocumentMarkdown(
    experimentId,
    'simulation_summary',
    { enabled: showViewer && isCompleted },
  );

  const handleSummaryClick = () => {
    if (isCompleted) {
      setShowViewer(true);
    }
  };

  // Loading
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 text-violet-500 mx-auto mb-3 animate-spin" />
        <p className="text-slate-500">Carregando resultados...</p>
      </div>
    );
  }

  // No results yet
  if (!simulationRun) {
    return (
      <div className="text-center py-12">
        <Activity className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">
          Nenhuma simulação realizada ainda.
        </p>
        <p className="text-sm text-slate-400 mt-1">
          Execute a simulação na aba &quot;Análise Quanti&quot;.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results */}
      <SimulationResults run={simulationRun} />

      {/* Action buttons — sticky bottom */}
      <div className="sticky bottom-0 bg-white/95 backdrop-blur-sm z-10 -mx-6 px-6 flex items-center justify-end gap-3 pt-4 pb-4 border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        <Button
          size="sm"
          variant="outline"
          onClick={handleSummaryClick}
          disabled={isGenerating || !isCompleted}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              Gerando Resumo...
            </>
          ) : (
            <>
              <BarChart3 className="w-4 h-4 mr-1" />
              Ver Resumo da Simulação
            </>
          )}
        </Button>
        <Button
          size="sm"
          onClick={onGenerateGuide}
          className="btn-primary"
        >
          <FileText className="w-4 h-4 mr-1" />
          Gerar roteiro de entrevista
        </Button>
      </div>

      {/* Document Viewer for simulation summary */}
      <DocumentViewer
        isOpen={showViewer}
        onClose={() => setShowViewer(false)}
        documentType="simulation_summary"
        markdownContent={markdownContent ?? undefined}
        isLoading={isLoadingMarkdown}
        status={isCompleted ? 'completed' : undefined}
      />
    </div>
  );
}
