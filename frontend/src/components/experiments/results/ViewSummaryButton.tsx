/**
 * ViewSummaryButton Component
 *
 * Button to open the executive summary viewer.
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2)
 *   - Viewer: DocumentViewer.tsx (shared component with PDF download)
 *
 * Features:
 *   - Disabled if no summary available
 *   - Loading indicator while generating
 *   - "Novo" badge for recently generated summaries
 *   - PDF download functionality via DocumentViewer
 */

import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDocumentAvailability, useGenerateDocument, useDocumentMarkdown } from '@/hooks/use-documents';
import { DocumentViewer } from '@/components/shared/DocumentViewer';
import { toast } from 'sonner';

interface ViewSummaryButtonProps {
  experimentId: string;
}

export function ViewSummaryButton({ experimentId }: ViewSummaryButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: availability, isLoading } = useDocumentAvailability(experimentId);
  const generateMutation = useGenerateDocument(experimentId, 'executive_summary');
  const { data: markdown } = useDocumentMarkdown(experimentId, 'executive_summary', { enabled: isModalOpen });

  const summary = availability?.executive_summary;

  // Check if summary is new (generated in last 5 minutes)
  const isNew =
    summary?.available &&
    summary?.generated_at &&
    Date.now() - new Date(summary.generated_at).getTime() < 5 * 60 * 1000;

  // Determine button state
  const isAvailable = summary?.available;
  const isGenerating = summary?.status === 'generating' || generateMutation.isPending;
  const canGenerate = !isAvailable && !isGenerating;

  // Button should be disabled if: loading or failed
  const isDisabled = isLoading || summary?.status === 'failed';

  const handleClick = () => {
    if (canGenerate) {
      // Start generation
      generateMutation.mutate(undefined, {
        onSuccess: () => {
          toast.success('Resumo executivo em geração', {
            description: 'O documento estará disponível em alguns segundos.',
          });
        },
        onError: (error) => {
          toast.error('Erro ao gerar resumo', {
            description: error instanceof Error ? error.message : 'Tente novamente mais tarde.',
          });
        },
      });
    } else {
      // Open modal to view
      setIsModalOpen(true);
    }
  };

  return (
    <>
      <Button
        onClick={handleClick}
        disabled={isDisabled}
        className="btn-primary relative"
      >
        {isGenerating ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Gerando...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            {canGenerate ? 'Gerar Resumo Executivo' : 'Ver Resumo Executivo'}
          </>
        )}
        {isNew && summary?.status === 'completed' && (
          <Badge className="badge-success ml-2 absolute -top-2 -right-2">Novo</Badge>
        )}
      </Button>

      <DocumentViewer
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        documentType="executive_summary"
        markdownContent={markdown}
        status={summary?.status === 'generating' ? 'generating' : isAvailable ? 'completed' : 'pending'}
        isLoading={generateMutation.isPending}
      />
    </>
  );
}
