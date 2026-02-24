/**
 * SimulationReport component.
 *
 * Displays the LLM-generated analysis report for the latest simulation batch.
 * Shows a skeleton while loading, a subtle message if report is not yet ready,
 * and renders the markdown content with a model/date badge when available.
 *
 * References:
 *   - Hook: src/hooks/use-quantitative-analysis.ts
 *   - Component: src/components/shared/DocumentViewer.tsx (markdown pattern)
 */

import { Loader2, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSimulationReport } from '@/hooks/use-quantitative-analysis';

interface SimulationReportProps {
  experimentId: string;
}

export function SimulationReport({ experimentId }: SimulationReportProps) {
  const { data: report, isLoading } = useSimulationReport(experimentId);

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-5 w-48 bg-slate-100 rounded" />
        <div className="h-4 w-full bg-slate-100 rounded" />
        <div className="h-4 w-5/6 bg-slate-100 rounded" />
        <div className="h-4 w-4/6 bg-slate-100 rounded" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400 py-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Relatório sendo gerado...</span>
      </div>
    );
  }

  const formattedDate = new Date(report.created_at).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-violet-500" />
          <h3 className="text-sm font-semibold text-slate-700">Relatório de Análise</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-0.5 bg-slate-100 rounded-full">{report.model}</span>
          <span>{formattedDate}</span>
        </div>
      </div>

      {/* Markdown content */}
      <div className="markdown-content text-sm text-slate-700 leading-relaxed">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {report.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
