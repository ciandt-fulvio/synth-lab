/**
 * ViewSummaryButton Component
 *
 * Button to open the executive summary modal.
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2)
 *   - Modal: ExecutiveSummaryModal.tsx
 *
 * Features:
 *   - Disabled if no summary available
 *   - Loading indicator while generating
 *   - "Novo" badge for recently generated summaries
 */

import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useExecutiveSummary } from '@/hooks/use-executive-summary';
import { ExecutiveSummaryModal } from './ExecutiveSummaryModal';

interface ViewSummaryButtonProps {
  experimentId: string;
}

export function ViewSummaryButton({ experimentId }: ViewSummaryButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: summary, isLoading } = useExecutiveSummary(experimentId);

  // Check if summary is new (generated in last 5 minutes)
  const isNew =
    summary &&
    summary.status === 'completed' &&
    Date.now() - new Date(summary.generation_timestamp).getTime() < 5 * 60 * 1000;

  // Button should be disabled if: loading, no data, or failed
  const isDisabled = isLoading || !summary || summary.status === 'failed';

  return (
    <>
      <Button
        onClick={() => setIsModalOpen(true)}
        disabled={isDisabled}
        className="btn-primary relative"
      >
        {summary?.status === 'pending' || summary?.status === 'partial' ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Gerando...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            Ver Resumo Executivo
          </>
        )}
        {isNew && summary.status === 'completed' && (
          <Badge className="badge-success ml-2 absolute -top-2 -right-2">Novo</Badge>
        )}
      </Button>

      <ExecutiveSummaryModal
        experimentId={experimentId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}
