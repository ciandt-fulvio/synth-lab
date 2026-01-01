/**
 * DocumentViewer component for synth-lab.
 *
 * Standardized popup for viewing experiment documents (summary, prfaq, executive_summary).
 * Based on MarkdownPopup with consistent styling.
 *
 * Visual specifications:
 * - Dialog: sm:max-w-[70vw] h-[80vh]
 * - Content: bg-gray-50 rounded-md px-6 py-4
 * - Markdown: .markdown-content class (globals.css)
 * - Fonts: Inter (body), Georgia serif (headings)
 */

import { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, AlertCircle, FileText, Newspaper, Sparkles, Download } from "lucide-react";
import { toast } from "sonner";
import type { DocumentType, DocumentStatus } from "@/types/document";
import { DOCUMENT_TYPE_LABELS } from "@/types/document";
import { generatePdfFromElement, generatePdfFilename } from "@/lib/pdf-utils";

interface DocumentViewerProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Document type for title and icon */
  documentType: DocumentType;
  /** Markdown content to display */
  markdownContent?: string;
  /** Whether content is loading */
  isLoading?: boolean;
  /** Current document status */
  status?: DocumentStatus;
  /** Error message if failed */
  errorMessage?: string;
  /** Optional custom title suffix */
  titleSuffix?: string;
}

/** Get icon component for document type */
function getDocumentIcon(documentType: DocumentType) {
  switch (documentType) {
    case 'summary':
      return <FileText className="h-5 w-5 text-indigo-600" />;
    case 'prfaq':
      return <Newspaper className="h-5 w-5 text-violet-600" />;
    case 'executive_summary':
      return <Sparkles className="h-5 w-5 text-amber-600" />;
  }
}

/**
 * DocumentViewer - Standardized document viewing popup.
 *
 * Features:
 * - Consistent styling across all document types
 * - Loading state with spinner
 * - Error state with message
 * - Markdown rendering with GFM support
 */
export function DocumentViewer({
  isOpen,
  onClose,
  documentType,
  markdownContent,
  isLoading,
  status,
  errorMessage,
  titleSuffix,
}: DocumentViewerProps) {
  // State for PDF generation
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

  // Ref to markdown content for PDF capture
  const contentRef = useRef<HTMLDivElement>(null);

  const title = DOCUMENT_TYPE_LABELS[documentType];
  const fullTitle = titleSuffix ? `${title} - ${titleSuffix}` : title;
  const icon = getDocumentIcon(documentType);

  // Determine content to render
  const isGenerating = status === 'generating' || isLoading;
  const isFailed = status === 'failed';
  const hasContent = markdownContent && markdownContent.length > 0;

  // Handle PDF download
  const handleDownloadPdf = async () => {
    if (!contentRef.current) {
      toast.error('Erro ao gerar PDF', {
        description: 'Conteúdo não encontrado.',
      });
      return;
    }

    setIsGeneratingPdf(true);

    try {
      const filename = generatePdfFilename(documentType, titleSuffix);
      await generatePdfFromElement(contentRef.current, filename);

      toast.success('PDF gerado com sucesso!');
    } catch (error) {
      console.error('PDF generation failed:', error);
      toast.error('Erro ao gerar PDF', {
        description: 'Tente novamente ou reduza o tamanho do documento.',
      });
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[70vw] h-[80vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              {icon}
              {fullTitle}
            </DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDownloadPdf}
              disabled={isGenerating || isFailed || !hasContent || isGeneratingPdf}
              aria-label="Download PDF"
            >
              {isGeneratingPdf ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
            </Button>
          </div>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto px-6 py-4 bg-gray-50 rounded-md">
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-600">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
              <span>Gerando {title.toLowerCase()}...</span>
            </div>
          ) : isFailed ? (
            <div className="flex flex-col items-center justify-center h-full text-red-600">
              <AlertCircle className="h-8 w-8 mb-3" />
              <span className="font-medium">Falha ao gerar documento</span>
              {errorMessage && (
                <span className="text-sm text-red-500 mt-2">{errorMessage}</span>
              )}
            </div>
          ) : hasContent ? (
            <article ref={contentRef} className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdownContent}
              </ReactMarkdown>
            </article>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
              <FileText className="h-8 w-8 mb-3 text-slate-400" />
              <span>Documento não disponível</span>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default DocumentViewer;
