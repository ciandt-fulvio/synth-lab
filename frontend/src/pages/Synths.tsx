/**
 * Synths page - Synth Group Catalog.
 *
 * Shows synth groups as cards. Clicking a card navigates to the group detail page.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US8)
 *   - Custom groups: specs/030-custom-synth-groups/spec.md (US2)
 */

import { useState } from 'react';
import { SynthGroupList } from '@/components/synths/SynthGroupList';
import { CreateSynthGroupModal } from '@/components/synths/CreateSynthGroupModal';
import { Users, Plus } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import { Button } from '@/components/ui/button';

export default function Synths() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const { data: groupsData, isLoading: groupsLoading, refetch } = useSynthGroups({ limit: 100 });

  const hasGroups = !groupsLoading && groupsData && groupsData.data.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Catalogo de Synths" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        {hasGroups && (
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-xl text-white shadow-lg shadow-indigo-200/50">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Grupos de Synths</h2>
                <p className="text-sm text-slate-500">
                  Cada grupo representa uma populacao com perfis demograficos e comportamentais unicos
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
        )}

        {/* Synth Groups Grid */}
        <SynthGroupList
          groups={groupsData?.data ?? []}
          isLoading={groupsLoading}
          onCreateClick={() => setCreateModalOpen(true)}
        />
      </main>

      <CreateSynthGroupModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={() => refetch()}
      />
    </div>
  );
}
