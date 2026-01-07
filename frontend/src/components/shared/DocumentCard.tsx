/**
 * DocumentCard component.
 *
 * Generic card for documents (summary or PRFAQ) with generation,
 * viewing, and regeneration capabilities.
 *
 * Used by both ExplorationDetail and InterviewDetail pages.
 *
 * References:
 *   - Spec: specs/028-exploration-summary/spec.md
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { DocumentViewer } from '@/components/shared/DocumentViewer';
import {
  FileText,
  Newspaper,
  Loader2,
  RefreshCw,
  AlertCircle,
  Eye,
  Sparkles,
} from 'lucide-react';
import type { ExperimentDocument, DocumentStatus } from '@/types/document';

/** Configuration for a document type */
export interface DocumentTypeConfig {
  title: string;
  description: string;
  icon: typeof FileText;
  iconColor: string;
  generateLabel: string;
  regenerateLabel: string;
  defaultDisabledReason: string;
  viewerTitleSuffix: string;
}

/** All supported document types */
export type SupportedDocumentType =
  | 'exploration_summary'
  | 'exploration_prfaq'
  | 'research_summary'
  | 'research_prfaq';

/** Document configurations by type */
export const DOCUMENT_CONFIGS: Record<SupportedDocumentType, DocumentTypeConfig> = {
  exploration_summary: {
    title: 'Resumo da Exploração',
    description: 'Narrativa descrevendo o estado otimizado após aplicar as melhorias',
    icon: FileText,
    iconColor: 'text-indigo-600',
    generateLabel: 'Gerar Resumo',
    regenerateLabel: 'Regenerar',
    defaultDisabledReason: 'Aguardando conclusão da exploração',
    viewerTitleSuffix: 'Exploração',
  },
  exploration_prfaq: {
    title: 'PR-FAQ',
    description: 'Documento formal com Press Release, FAQ e Recomendações',
    icon: Newspaper,
    iconColor: 'text-violet-600',
    generateLabel: 'Gerar PR-FAQ',
    regenerateLabel: 'Regenerar',
    defaultDisabledReason: 'Gere o resumo primeiro',
    viewerTitleSuffix: 'Exploração',
  },
  research_summary: {
    title: 'Resumo de Entrevista',
    description: 'Síntese das entrevistas com principais insights e descobertas',
    icon: FileText,
    iconColor: 'text-indigo-600',
    generateLabel: 'Gerar Resumo',
    regenerateLabel: 'Regenerar',
    defaultDisabledReason: 'Aguardando conclusão das entrevistas',
    viewerTitleSuffix: 'Entrevista',
  },
  research_prfaq: {
    title: 'PR-FAQ de Entrevista',
    description: 'Documento formal com Press Release, FAQ e Recomendações',
    icon: Newspaper,
    iconColor: 'text-violet-600',
    generateLabel: 'Gerar PR-FAQ',
    regenerateLabel: 'Regenerar',
    defaultDisabledReason: 'Gere o resumo primeiro',
    viewerTitleSuffix: 'Entrevista',
  },
};

interface DocumentCardProps {
  /** Document type */
  documentType: SupportedDocumentType;
  /** Existing document, if any */
  document?: ExperimentDocument | null;
  /** Whether document is loading */
  isLoading?: boolean;
  /** Whether generation is in progress */
  isGenerating?: boolean;
  /** Whether source is in a completed state (enables generation) */
  canGenerate?: boolean;
  /** Callback to generate document */
  onGenerate?: () => void;
  /** Custom message explaining why generation is disabled */
  disabledReason?: string;
  /** Additional CSS classes */
  className?: string;
}

export function DocumentCard({
  documentType,
  document,
  isLoading = false,
  isGenerating = false,
  canGenerate = false,
  onGenerate,
  disabledReason,
  className = '',
}: DocumentCardProps) {
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  const config = DOCUMENT_CONFIGS[documentType];
  const Icon = config.icon;

  // Determine document state
  const hasDocument = document !== null && document !== undefined;
  const isCompleted = hasDocument && document.status === 'completed';
  const isFailed = hasDocument && document.status === 'failed';
  const isDocGenerating = hasDocument && document.status === 'generating';

  // Show regenerate if document exists (completed or failed)
  const showRegenerate = hasDocument && (isCompleted || isFailed);

  // Disabled if generating, loading, or source not completed
  const isDisabled = isGenerating || isLoading || isDocGenerating || !canGenerate;

  return (
    <>
      <Card className={`border-slate-200 ${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
                <Icon className={`h-5 w-5 ${config.iconColor}`} />
              </div>
              <div>
                <CardTitle className="text-base font-semibold text-slate-900">
                  {config.title}
                </CardTitle>
                <p className="text-sm text-slate-500 mt-0.5">
                  {config.description}
                </p>
              </div>
            </div>

            {/* Status indicator */}
            {isDocGenerating && (
              <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Gerando...</span>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          )}

          {/* Error state */}
          {!isLoading && isFailed && (
            <div className="bg-red-50 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-700">
                    Falha ao gerar documento
                  </p>
                  {document?.error_message && (
                    <p className="text-sm text-red-600 mt-1">
                      {document.error_message}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Completed state */}
          {!isLoading && isCompleted && (
            <div className="bg-green-50 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-700">
                    Documento gerado com sucesso
                  </p>
                  {document?.generated_at && (
                    <p className="text-sm text-green-600 mt-1">
                      Gerado em: {new Date(document.generated_at).toLocaleString('pt-BR')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3">
            {/* View button - only if completed */}
            {isCompleted && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsViewerOpen(true)}
                className="gap-2"
              >
                <Eye className="h-4 w-4" />
                Visualizar
              </Button>
            )}

            {/* Generate/Regenerate button with tooltip when disabled */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className={isDisabled && !isGenerating && !isDocGenerating ? 'cursor-not-allowed' : ''}>
                    <Button
                      variant={showRegenerate ? 'outline' : 'default'}
                      size="sm"
                      onClick={onGenerate}
                      disabled={isDisabled}
                      className={`gap-2 ${
                        showRegenerate
                          ? 'border-slate-300 hover:border-slate-400'
                          : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700'
                      } ${isDisabled && !isGenerating && !isDocGenerating ? 'pointer-events-none' : ''}`}
                    >
                      {isGenerating || isDocGenerating ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Gerando...
                        </>
                      ) : showRegenerate ? (
                        <>
                          <RefreshCw className="h-4 w-4" />
                          {config.regenerateLabel}
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4" />
                          {config.generateLabel}
                        </>
                      )}
                    </Button>
                  </span>
                </TooltipTrigger>
                {isDisabled && !isGenerating && !isDocGenerating && (
                  <TooltipContent>
                    <p>{disabledReason || config.defaultDisabledReason}</p>
                  </TooltipContent>
                )}
              </Tooltip>
            </TooltipProvider>
          </div>
        </CardContent>
      </Card>

      {/* Document viewer dialog */}
      <DocumentViewer
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
        documentType={documentType}
        markdownContent={document?.markdown_content}
        isLoading={isLoading}
        status={document?.status as DocumentStatus}
        errorMessage={document?.error_message}
        titleSuffix={config.viewerTitleSuffix}
      />
    </>
  );
}

export default DocumentCard;
