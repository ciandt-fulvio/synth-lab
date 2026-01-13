/**
 * T032 Synths page - Synth Catalog.
 *
 * Synth catalog page with Research Observatory aesthetic.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US8)
 *   - Custom groups: specs/030-custom-synth-groups/spec.md (US2)
 */

import { useState, useEffect } from 'react';
import { SynthList } from '@/components/synths/SynthList';
import { SynthGroupList } from '@/components/synths/SynthGroupList';
import {
  SynthGroupDetailView,
  SynthGroupDetailSkeleton,
} from '@/components/synths/SynthGroupDetail';
import { CreateSynthGroupModal } from '@/components/synths/CreateSynthGroupModal';
import { Users, Plus, ChevronDown, ChevronRight, Layers, X } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useSynthGroups, useSynthGroup } from '@/hooks/use-synth-groups';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

// =============================================================================
// Animated Section Component
// =============================================================================

interface AnimatedSectionProps {
  children: React.ReactNode;
  delay?: number;
}

function AnimatedSection({ children, delay = 0 }: AnimatedSectionProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`transition-all duration-500 ease-out ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      {children}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function Synths() {
  const [selectedGroupId, setSelectedGroupId] = useState<string | undefined>(undefined);
  const [detailGroupId, setDetailGroupId] = useState<string | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const { data: groupsData, isLoading: groupsLoading, refetch } = useSynthGroups({ limit: 100 });
  const { data: groupDetail, isLoading: detailLoading } = useSynthGroup(detailGroupId ?? '');

  const handleGroupSelect = (groupId: string) => {
    // Toggle selection: if already selected, deselect
    if (selectedGroupId === groupId) {
      setSelectedGroupId(undefined);
    } else {
      setSelectedGroupId(groupId);
    }
  };

  const handleViewDetails = (groupId: string) => {
    setDetailGroupId(groupId);
  };

  const handleCreateSuccess = () => {
    refetch();
  };

  const selectedGroup = groupsData?.data.find((g) => g.id === selectedGroupId);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Catálogo de Synths" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <AnimatedSection delay={0}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-xl text-white shadow-lg shadow-indigo-200/50">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Synths</h2>
                <p className="text-sm text-slate-500">
                  Cada synth representa um perfil demográfico e comportamental único
                </p>
              </div>
            </div>

            <Button
              onClick={() => setCreateModalOpen(true)}
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-lg shadow-indigo-200/50"
            >
              <Plus className="h-4 w-4 mr-2" />
              Novo Grupo
            </Button>
          </div>
        </AnimatedSection>

        {/* Synth Groups Section */}
        <AnimatedSection delay={50}>
          <Collapsible open={groupsExpanded} onOpenChange={setGroupsExpanded} className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <CollapsibleTrigger asChild>
                <button className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
                  {groupsExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <Layers className="h-4 w-4" />
                  <span>Grupos de Synths</span>
                  {groupsData && (
                    <span className="text-slate-400">({groupsData.data.length})</span>
                  )}
                </button>
              </CollapsibleTrigger>
              {selectedGroupId && (
                <button
                  onClick={() => setSelectedGroupId(undefined)}
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Limpar filtro
                </button>
              )}
            </div>
            <CollapsibleContent>
              <SynthGroupList
                groups={groupsData?.data ?? []}
                selectedId={selectedGroupId}
                onSelect={handleGroupSelect}
                onViewDetails={handleViewDetails}
                isLoading={groupsLoading}
                onCreateClick={() => setCreateModalOpen(true)}
              />
            </CollapsibleContent>
          </Collapsible>
        </AnimatedSection>

        {/* Synth List */}
        <AnimatedSection delay={100}>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            {selectedGroup && (
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
                <div className="flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-indigo-600" />
                  <span className="font-medium text-slate-900">{selectedGroup.name}</span>
                  <span className="text-slate-500">
                    ({selectedGroup.synth_count} synths)
                  </span>
                </div>
              </div>
            )}
            <SynthList selectedGroupId={selectedGroupId} />
          </div>
        </AnimatedSection>
      </main>

      {/* Create Synth Group Modal */}
      <CreateSynthGroupModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={handleCreateSuccess}
      />

      {/* Group Detail Sheet */}
      <Sheet open={!!detailGroupId} onOpenChange={(open) => !open && setDetailGroupId(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          <SheetHeader className="mb-4">
            <SheetTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-600" />
              Detalhes do Grupo
            </SheetTitle>
          </SheetHeader>
          {detailLoading ? (
            <SynthGroupDetailSkeleton />
          ) : groupDetail ? (
            <SynthGroupDetailView group={groupDetail} />
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}
