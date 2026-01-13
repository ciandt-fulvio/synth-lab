/**
 * T026 SynthGroupList component - Enhanced UI.
 *
 * Grid list of synth group cards with staggered animations and improved states.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md (US2)
 *   - Types: src/types/synthGroup.ts
 */

import { SynthGroupCard } from './SynthGroupCard';
import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';
import { Users, Plus, Sparkles } from 'lucide-react';
import type { SynthGroupSummary } from '@/types/synthGroup';

interface SynthGroupListProps {
  groups: SynthGroupSummary[];
  selectedId?: string;
  onSelect: (groupId: string) => void;
  onViewDetails?: (groupId: string) => void;
  isLoading?: boolean;
  onCreateClick?: () => void;
}

function LoadingSkeleton() {
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <Card
          key={i}
          className="p-6 border-2 border-slate-200/60 animate-pulse"
          style={{
            animationDelay: `${i * 100}ms`,
            animationDuration: '1.5s',
          }}
        >
          <div className="flex items-center gap-3 mb-4">
            <Skeleton className="h-10 w-10 rounded-xl" />
            <div className="flex-1">
              <Skeleton className="h-5 w-32 mb-2" />
            </div>
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mb-4" />
          <div className="flex items-center justify-between mt-4">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-7 w-20 rounded-lg" />
          </div>
        </Card>
      ))}
    </div>
  );
}

function EmptyState({ onCreateClick }: { onCreateClick?: () => void }) {
  return (
    <div className="text-center py-16 px-4">
      <div className="mx-auto w-20 h-20 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center mb-5 shadow-sm">
        <Users className="h-10 w-10 text-slate-400" />
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-2">
        Nenhum grupo encontrado
      </h3>
      <p className="text-sm text-slate-600 max-w-md mx-auto mb-6 leading-relaxed">
        Crie seu primeiro grupo de synths com distribuições demográficas customizadas
        para simular diferentes perfis de usuários.
      </p>
      {onCreateClick && (
        <button
          onClick={onCreateClick}
          className="
            inline-flex items-center gap-2 px-5 py-2.5
            bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600
            hover:from-blue-700 hover:via-indigo-700 hover:to-violet-700
            text-white text-sm font-semibold rounded-xl
            shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30
            transition-all duration-200
            hover:scale-105
          "
        >
          <Plus className="h-4 w-4" />
          Criar Primeiro Grupo
          <Sparkles className="h-4 w-4 ml-0.5" />
        </button>
      )}
    </div>
  );
}

export function SynthGroupList({
  groups,
  selectedId,
  onSelect,
  onViewDetails,
  isLoading = false,
  onCreateClick,
}: SynthGroupListProps) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (groups.length === 0) {
    return <EmptyState onCreateClick={onCreateClick} />;
  }

  // Sort groups: default first, then by created_at DESC
  const sortedGroups = [...groups].sort((a, b) => {
    if (a.id === 'grp_default') return -1;
    if (b.id === 'grp_default') return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {sortedGroups.map((group, index) => (
        <div
          key={group.id}
          className="animate-in fade-in slide-in-from-bottom-4"
          style={{
            animationDelay: `${index * 50}ms`,
            animationDuration: '400ms',
            animationFillMode: 'backwards',
          }}
        >
          <SynthGroupCard
            group={group}
            onClick={onSelect}
            onViewDetails={onViewDetails}
            isSelected={selectedId === group.id}
          />
        </div>
      ))}
    </div>
  );
}
