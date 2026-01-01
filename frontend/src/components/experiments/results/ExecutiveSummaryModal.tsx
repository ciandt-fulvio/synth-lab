/**
 * ExecutiveSummaryModal Component
 *
 * Dialog (popup) displaying executive summary markdown content.
 * Follows MarkdownPopup pattern for consistent styling.
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2)
 *   - Pattern: components/shared/MarkdownPopup.tsx
 *
 * Features:
 *   - Centered dialog layout (not side drawer)
 *   - Loading state with spinner
 *   - Markdown rendering with GFM support
 *   - Consistent styling with other document popups
 */

import { Loader2, Sparkles, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useDocumentMarkdown } from '@/hooks/use-documents';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ExecutiveSummaryModalProps {
  experimentId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExecutiveSummaryModal({
  experimentId,
  isOpen,
  onClose,
}: ExecutiveSummaryModalProps) {
  const { data: markdown, isLoading, error } = useDocumentMarkdown(
    experimentId,
    'executive_summary',
    { enabled: isOpen }
  );

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[70vw] h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-amber-600" />
            Resumo Executivo
          </DialogTitle>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto px-6 py-4 bg-gray-50 rounded-md">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-slate-600">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
              <span>Carregando resumo executivo...</span>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-red-600">
              <AlertCircle className="h-8 w-8 mb-3" />
              <span className="font-medium">Erro ao carregar documento</span>
              <span className="text-sm text-red-500 mt-2">
                {error.message?.includes('404')
                  ? 'Resumo executivo não encontrado. Gere um resumo primeiro.'
                  : 'Tente novamente mais tarde.'}
              </span>
            </div>
          )}

          {/* Content */}
          {markdown && !isLoading && (
            <article className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdown}
              </ReactMarkdown>
            </article>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
