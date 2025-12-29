// src/components/synths/SynthList.tsx

import { useState, useEffect } from 'react';
import { SynthCard } from './SynthCard';
import { SynthDetailDialog } from './SynthDetailDialog';
import { useSynthsList } from '@/hooks/use-synths';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Users } from 'lucide-react';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/ui/pagination';

const ITEMS_PER_PAGE = 45;

interface SynthListProps {
  selectedGroupId?: string;
}

export function SynthList({ selectedGroupId }: SynthListProps) {
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);

  // Reset to first page when filter changes
  useEffect(() => {
    setCurrentPage(0);
  }, [selectedGroupId]);

  // Fetch synth groups for displaying group names on cards
  const { data: groupsData } = useSynthGroups({ limit: 100 });

  const { data, isLoading, error } = useSynthsList({
    limit: ITEMS_PER_PAGE,
    offset: currentPage * ITEMS_PER_PAGE,
    synth_group_id: selectedGroupId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Erro ao carregar synths: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Users className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Nenhum synth encontrado</h3>
        <p className="text-sm text-muted-foreground">
          Não há synths disponíveis no momento
        </p>
      </div>
    );
  }

  const totalPages = Math.ceil(data.pagination.total / ITEMS_PER_PAGE);
  const hasPrevious = currentPage > 0;
  const hasNext = currentPage < totalPages - 1;

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      // Show all pages if total is small
      for (let i = 0; i < totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(0);

      // Calculate range around current page
      const start = Math.max(1, currentPage - 1);
      const end = Math.min(totalPages - 2, currentPage + 1);

      // Add ellipsis after first page if needed
      if (start > 1) {
        pages.push('ellipsis');
      }

      // Add pages around current
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // Add ellipsis before last page if needed
      if (end < totalPages - 2) {
        pages.push('ellipsis');
      }

      // Always show last page
      pages.push(totalPages - 1);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();

  return (
    <>
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.data.map((synth) => (
          <SynthCard
            key={synth.id}
            synth={synth}
            onClick={(id) => setSelectedSynthId(id)}
            groupName={synth.synth_group_id && groupsData?.data
              ? groupsData.data.find(g => g.id === synth.synth_group_id)?.name
              : undefined}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="px-4 pb-4 pt-2">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => hasPrevious && setCurrentPage(currentPage - 1)}
                  className={!hasPrevious ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>

              {pageNumbers.map((page, idx) =>
                page === 'ellipsis' ? (
                  <PaginationItem key={`ellipsis-${idx}`}>
                    <PaginationEllipsis />
                  </PaginationItem>
                ) : (
                  <PaginationItem key={page}>
                    <PaginationLink
                      onClick={() => setCurrentPage(page)}
                      isActive={currentPage === page}
                      className="cursor-pointer"
                    >
                      {page + 1}
                    </PaginationLink>
                  </PaginationItem>
                )
              )}

              <PaginationItem>
                <PaginationNext
                  onClick={() => hasNext && setCurrentPage(currentPage + 1)}
                  className={!hasNext ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>

          <div className="text-center mt-4 text-sm text-muted-foreground">
            Mostrando {data.pagination.offset + 1} a {Math.min(data.pagination.offset + data.pagination.limit, data.pagination.total)} de {data.pagination.total} synths
          </div>
        </div>
      )}

      <SynthDetailDialog
        synthId={selectedSynthId}
        open={!!selectedSynthId}
        onOpenChange={(open) => {
          if (!open) setSelectedSynthId(null);
        }}
      />
    </>
  );
}
