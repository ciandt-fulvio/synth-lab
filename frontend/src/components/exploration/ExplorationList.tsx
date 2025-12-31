/**
 * ExplorationList component.
 *
 * List of explorations for an experiment.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US6)
 */

import { ExplorationListItem } from './ExplorationListItem';
import type { ExplorationSummary } from '@/types/exploration';
import { Skeleton } from '@/components/ui/skeleton';
import { TreeDeciduous } from 'lucide-react';

interface ExplorationListProps {
  explorations: ExplorationSummary[] | undefined;
  experimentId: string;
  isLoading?: boolean;
}

export function ExplorationList({
  explorations,
  experimentId,
  isLoading,
}: ExplorationListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (!explorations || explorations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <TreeDeciduous className="h-10 w-10 text-slate-300 mb-3" />
        <p className="text-muted-foreground text-sm">
          Nenhuma exploração encontrada
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Inicie uma exploração para otimizar cenários com IA
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {explorations.map((exploration) => (
        <ExplorationListItem
          key={exploration.id}
          exploration={exploration}
          experimentId={experimentId}
        />
      ))}
    </div>
  );
}
