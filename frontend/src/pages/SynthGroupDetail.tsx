/**
 * SynthGroupDetail page.
 *
 * Shows a tabbed view with statistics (demographics + sensitivities)
 * and the paginated synth list for a given group.
 *
 * References:
 *   - Route: /synths/groups/:groupId
 *   - API: GET /synth-groups/{group_id}/statistics
 *   - Components: DemographicCharts, SensitivityHistograms, SynthList
 */

import { useParams } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { DemographicCharts } from '@/components/synths/DemographicCharts';
import { SensitivityHistograms } from '@/components/synths/SensitivityHistograms';
import { SynthList } from '@/components/synths/SynthList';
import { useSynthGroup, useSynthGroupStatistics } from '@/hooks/use-synth-groups';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, BarChart3, Users, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function SynthGroupDetail() {
  const { groupId } = useParams<{ groupId: string }>();
  const { data: group, isLoading: groupLoading } = useSynthGroup(groupId ?? '');
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
  } = useSynthGroupStatistics(groupId ?? '');

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={group?.name ?? 'Grupo de Synths'}
        backTo="/synths"
        breadcrumbs={[
          { label: 'Synths', href: '/synths' },
          { label: group?.name ?? 'Grupo' },
        ]}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Group header */}
        {groupLoading ? (
          <div className="mb-8">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        ) : group ? (
          <div className="flex items-center gap-4 mb-8">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-xl text-white shadow-lg shadow-indigo-200/50">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{group.name}</h2>
              {group.description && (
                <p className="text-sm text-slate-500 mt-1">{group.description}</p>
              )}
            </div>
          </div>
        ) : null}

        {/* Tabs */}
        <Tabs defaultValue="statistics">
          <TabsList>
            <TabsTrigger value="statistics" className="gap-1.5">
              <BarChart3 className="h-4 w-4" />
              Estatísticas
            </TabsTrigger>
            <TabsTrigger value="synths" className="gap-1.5">
              <User className="h-4 w-4" />
              Synths
              {group && (
                <Badge variant="secondary" className="ml-1 text-xs px-1.5 py-0">
                  {stats?.total_synths ?? group.synth_count}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Statistics tab */}
          <TabsContent value="statistics" className="mt-6">
            {/* Error state */}
            {statsError && !statsLoading && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <AlertCircle className="h-12 w-12 text-red-400 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  Erro ao carregar estatísticas
                </h3>
                <p className="text-sm text-slate-500">
                  Não foi possível carregar as estatísticas deste grupo.
                </p>
              </div>
            )}

            {/* Loading state */}
            {statsLoading && (
              <div className="space-y-6">
                <Skeleton className="h-6 w-32" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Skeleton className="h-72 rounded-lg" />
                  <Skeleton className="h-72 rounded-lg" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Skeleton className="h-56 rounded-lg" />
                  <Skeleton className="h-56 rounded-lg" />
                  <Skeleton className="h-56 rounded-lg" />
                </div>
                <Skeleton className="h-6 w-32 mt-8" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[...Array(9)].map((_, i) => (
                    <Skeleton key={i} className="h-52 rounded-lg" />
                  ))}
                </div>
              </div>
            )}

            {/* Charts */}
            {stats && !statsLoading && !statsError && (
              <div className="space-y-10">
                <DemographicCharts data={stats.demographics} />
                <SensitivityHistograms data={stats.sensitivities} />
              </div>
            )}
          </TabsContent>

          {/* Synths tab */}
          <TabsContent value="synths" className="mt-6">
            {groupId && <SynthList selectedGroupId={groupId} hideGroupName sortBy="interviewed_first" />}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
