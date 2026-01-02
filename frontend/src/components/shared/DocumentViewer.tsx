/**
 * DocumentViewer component for synth-lab.
 *
 * Standardized popup for viewing experiment documents (summary, prfaq, executive_summary).
 * Refined design with improved visual hierarchy and polished interactions.
 *
 * Features:
 * - PDF export: Download button with text label, loading state, and error handling
 * - Loading states: Elegant spinner with contextual messages
 * - Error states: User-friendly error messages with visual feedback
 * - Markdown rendering: GitHub-flavored markdown with .markdown-content styling
 * - Smart button states: Disabled when document is generating, failed, or empty
 *
 * Visual specifications:
 * - Dialog: sm:max-w-[70vw] h-[80vh] with refined header layout
 * - Header: Horizontal flex with icon container, title, and download button
 * - Icon: Contained in subtle gradient box with border
 * - Content: Gradient background (slate-50 to white) with border, max-width for readability
 * - Empty states: Circular icon containers with descriptive messages
 * - Fonts: Inter (body), Georgia serif (headings)
 *
 * PDF Generation:
 * - Uses html2canvas to capture markdown content as high-quality image (2x scale)
 * - Uses jsPDF to create A4 portrait PDF
 * - Filename format: {documentType}_{sanitized-title}.pdf
 * - Progress indication: Button shows "Gerando..." with spinner during generation
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

  /**
   * Handles PDF download for the document.
   *
   * Flow:
   * 1. Validates contentRef has a valid DOM element
   * 2. Sets isGeneratingPdf to true (shows loading spinner)
   * 3. Generates filename using documentType and titleSuffix
   * 4. Captures contentRef element as PDF using html2canvas + jsPDF
   * 5. Triggers browser download
   * 6. Shows success toast
   * 7. If error occurs: logs error, shows error toast with retry suggestion
   * 8. Finally: sets isGeneratingPdf to false (hides spinner)
   *
   * Error handling:
   * - Early return if contentRef is null (shouldn't happen, but defensive)
   * - Catch block handles html2canvas or jsPDF failures
   * - User-friendly Portuguese error messages
   */
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
        {/* Header with title and download button */}
        <DialogHeader className="flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-200 pr-12">
          <DialogTitle className="flex items-center gap-3 text-xl">
            <div className="p-2 rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
              {icon}
            </div>
            <span className="font-semibold text-slate-900">{fullTitle}</span>
          </DialogTitle>

          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadPdf}
            disabled={isGenerating || isFailed || !hasContent || isGeneratingPdf}
            className="gap-2 border-slate-300 hover:border-violet-400 hover:bg-violet-50 transition-all"
          >
            {isGeneratingPdf ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-violet-600" />
                <span className="text-sm font-medium">Gerando...</span>
              </>
            ) : (
              <>
                <Download className="h-4 w-4 text-violet-600" />
                <span className="text-sm font-medium">PDF</span>
              </>
            )}
          </Button>
        </DialogHeader>

        {/* Content area */}
        <div className="flex-grow overflow-y-auto px-6 py-6 bg-gradient-to-b from-slate-50 to-white rounded-lg border border-slate-100">
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="p-4 rounded-full bg-gradient-to-br from-indigo-50 to-violet-50 mb-4">
                <Loader2 className="h-10 w-10 animate-spin text-indigo-600" />
              </div>
              <span className="text-base font-medium text-slate-700">
                Gerando {title.toLowerCase()}...
              </span>
              <span className="text-sm text-slate-500 mt-1">
                Aguarde enquanto processamos o documento
              </span>
            </div>
          ) : isFailed ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="p-4 rounded-full bg-red-50 mb-4">
                <AlertCircle className="h-10 w-10 text-red-500" />
              </div>
              <span className="text-base font-semibold text-red-700">
                Falha ao gerar documento
              </span>
              {errorMessage && (
                <span className="text-sm text-red-600 mt-2 px-4 py-2 bg-red-50 rounded-md max-w-md text-center">
                  {errorMessage}
                </span>
              )}
            </div>
          ) : hasContent ? (
            <article ref={contentRef} className="markdown-content max-w-4xl mx-auto">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdownContent}
              </ReactMarkdown>
            </article>
          ) : (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="p-4 rounded-full bg-slate-100 mb-4">
                <FileText className="h-10 w-10 text-slate-400" />
              </div>
              <span className="text-base font-medium text-slate-600">
                Documento não disponível
              </span>
              <span className="text-sm text-slate-500 mt-1">
                Este documento ainda não foi gerado
              </span>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default DocumentViewer;
