/**
 * DocumentsList - List of experiment documents with sorting and filtering
 *
 * Features:
 * - Sort by document type (name) or date
 * - Filter by document type
 * - Badge indicators for each type
 * - Click to view document content
 */

import { useState, useMemo } from 'react';
import { FileText, Calendar, Filter, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useDocuments, useDocument } from '@/hooks/use-documents';
import { DocumentViewer } from '@/components/shared/DocumentViewer';
import { DOCUMENT_TYPE_LABELS } from '@/types/document';
import type { DocumentType, ExperimentDocumentSummary } from '@/types/document';

interface DocumentsListProps {
  experimentId: string;
}

// Document type badge colors
const DOCUMENT_TYPE_COLORS: Record<DocumentType, string> = {
  exploration_summary: 'bg-blue-100 text-blue-700 border-blue-200',
  exploration_prfaq: 'bg-cyan-100 text-cyan-700 border-cyan-200',
  research_summary: 'bg-purple-100 text-purple-700 border-purple-200',
  research_prfaq: 'bg-pink-100 text-pink-700 border-pink-200',
  executive_summary: 'bg-amber-100 text-amber-700 border-amber-200',
};

type SortOption = 'type' | 'date';

export function DocumentsList({ experimentId }: DocumentsListProps) {
  const { data: documents, isLoading } = useDocuments(experimentId);
  const [sortBy, setSortBy] = useState<SortOption>('date');
  const [filterType, setFilterType] = useState<DocumentType | 'all'>('all');
  const [selectedDocument, setSelectedDocument] = useState<ExperimentDocumentSummary | null>(null);

  // Fetch full document when selected
  const { data: fullDocument, isLoading: isLoadingDocument } = useDocument(
    experimentId,
    selectedDocument?.document_type ?? 'executive_summary',
    selectedDocument?.source_id ?? undefined
  );

  // Filtered and sorted documents
  const processedDocuments = useMemo(() => {
    if (!documents) return [];

    // Filter
    let filtered = documents;
    if (filterType !== 'all') {
      filtered = documents.filter((doc) => doc.document_type === filterType);
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === 'type') {
        return DOCUMENT_TYPE_LABELS[a.document_type].localeCompare(
          DOCUMENT_TYPE_LABELS[b.document_type]
        );
      } else {
        // Sort by date descending (newest first)
        return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
      }
    });

    return sorted;
  }, [documents, sortBy, filterType]);

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-500">Carregando documentos...</p>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">Nenhum relatório disponível ainda.</p>
        <p className="text-sm text-slate-400 mt-1">
          Relatórios serão gerados automaticamente após análises e explorações.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Sort dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              {sortBy === 'type' ? (
                <>
                  <FileText className="h-4 w-4" />
                  Ordenar por Nome
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4" />
                  Ordenar por Data
                </>
              )}
              <ChevronDown className="h-3 w-3 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuLabel>Ordenar por</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuRadioGroup value={sortBy} onValueChange={(val) => setSortBy(val as SortOption)}>
              <DropdownMenuRadioItem value="type">Nome do Documento</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="date">Data de Criação</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Filter dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <Filter className="h-4 w-4" />
              {filterType === 'all' ? 'Todos os Tipos' : DOCUMENT_TYPE_LABELS[filterType]}
              <ChevronDown className="h-3 w-3 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuLabel>Filtrar por Tipo</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuRadioGroup
              value={filterType}
              onValueChange={(val) => setFilterType(val as DocumentType | 'all')}
            >
              <DropdownMenuRadioItem value="all">Todos os Tipos</DropdownMenuRadioItem>
              <DropdownMenuSeparator />
              <DropdownMenuRadioItem value="exploration_summary">
                Resumo da Exploração
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="exploration_prfaq">
                PR-FAQ da Exploração
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="research_summary">
                Resumo da Pesquisa
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="research_prfaq">
                PR-FAQ da Pesquisa
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="executive_summary">
                Resumo Executivo
              </DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Results count */}
        <span className="text-sm text-slate-500 ml-auto">
          {processedDocuments.length} documento(s)
        </span>
      </div>

      {/* Documents list */}
      {processedDocuments.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 rounded-lg border border-dashed border-slate-200">
          <p className="text-slate-500">Nenhum documento encontrado com os filtros aplicados.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {processedDocuments.map((doc) => (
            <button
              key={doc.id}
              onClick={() => setSelectedDocument(doc)}
              className="w-full flex items-center gap-4 p-4 rounded-lg border bg-white transition-all hover:shadow-md hover:border-slate-300 text-left"
            >
              {/* Icon */}
              <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-slate-100">
                <FileText className="h-5 w-5 text-slate-600" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {/* Document type badge */}
                  <Badge
                    variant="outline"
                    className={`text-xs font-medium ${DOCUMENT_TYPE_COLORS[doc.document_type]}`}
                  >
                    {DOCUMENT_TYPE_LABELS[doc.document_type]}
                  </Badge>

                  {/* Status badge */}
                  {doc.status !== 'completed' && (
                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        doc.status === 'generating'
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : doc.status === 'failed'
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : 'bg-slate-50 text-slate-600 border-slate-200'
                      }`}
                    >
                      {doc.status === 'generating'
                        ? 'Gerando...'
                        : doc.status === 'failed'
                          ? 'Falhou'
                          : doc.status === 'pending'
                            ? 'Pendente'
                            : doc.status === 'partial'
                              ? 'Parcial'
                              : doc.status}
                    </Badge>
                  )}
                </div>

                {/* Date and model */}
                <div className="flex items-center gap-4 text-sm text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {format(new Date(doc.generated_at), "d 'de' MMMM 'de' yyyy 'às' HH:mm", {
                      locale: ptBR,
                    })}
                  </span>
                  <span className="text-xs">Modelo: {doc.model}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Document Viewer Dialog */}
      {selectedDocument && (
        <DocumentViewer
          isOpen={!!selectedDocument}
          onClose={() => setSelectedDocument(null)}
          documentType={selectedDocument.document_type}
          markdownContent={fullDocument?.markdown_content}
          isLoading={isLoadingDocument}
          status={fullDocument?.status ?? selectedDocument.status}
          errorMessage={fullDocument?.error_message}
        />
      )}
    </div>
  );
}
