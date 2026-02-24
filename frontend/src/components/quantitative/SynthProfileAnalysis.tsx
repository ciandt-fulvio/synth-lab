/**
 * SynthProfileAnalysis component.
 *
 * Compares adopter vs rejector profiles and shows demographic clusters
 * as a donut chart with adoption rate per cluster.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (SynthProfilesResponse)
 *   - Hook: useSynthProfiles
 */

import { Loader2, UserCheck, UserX } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { useSynthProfiles } from '@/hooks/use-quantitative-analysis';
import type { SynthGroupProfile } from '@/types/quantitative-analysis';

interface SynthProfileAnalysisProps {
  experimentId: string;
}

const CLUSTER_LABELS: Record<string, string> = {
  jovem_baixa_renda: 'Jovem + Baixa Renda',
  jovem_alta_renda: 'Jovem + Alta Renda',
  maduro_baixa_renda: 'Maduro + Baixa Renda',
  maduro_alta_renda: 'Maduro + Alta Renda',
};

const CLUSTER_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'];

function formatCurrency(val: number | null): string {
  if (val == null) return '–';
  return `R$ ${val.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`;
}

function ProfileCard({
  label,
  icon: Icon,
  profile,
  variant,
}: {
  label: string;
  icon: typeof UserCheck;
  profile: SynthGroupProfile;
  variant: 'adopter' | 'rejector';
}) {
  const isAdopter = variant === 'adopter';

  const gradientClass = isAdopter
    ? 'from-emerald-50 to-teal-50'
    : 'from-red-50 to-rose-50';
  const borderClass = isAdopter ? 'border-emerald-200' : 'border-red-200';
  const iconBgClass = isAdopter ? 'bg-emerald-100' : 'bg-red-100';
  const iconColorClass = isAdopter ? 'text-emerald-600' : 'text-red-500';
  const accentClass = isAdopter ? 'text-emerald-700' : 'text-red-600';
  const chipClass = isAdopter
    ? 'bg-emerald-100/70 text-emerald-800'
    : 'bg-red-100/70 text-red-800';

  return (
    <div className={`rounded-xl border ${borderClass} bg-gradient-to-br ${gradientClass} p-5 flex flex-col gap-4`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg ${iconBgClass} flex items-center justify-center`}>
            <Icon className={`w-4 h-4 ${iconColorClass}`} />
          </div>
          <span className="text-sm font-semibold text-slate-700">{label}</span>
        </div>
        <span className="text-xs text-slate-400 font-medium">{profile.count} synths</span>
      </div>

      {/* Hero number */}
      <div>
        <p className={`text-5xl font-black tracking-tight ${accentClass}`}>
          {profile.avg_adoption.toFixed(1)}
          <span className="text-2xl font-bold ml-0.5">%</span>
        </p>
        <p className="text-xs text-slate-500 mt-1">taxa média de adoção</p>
      </div>

      {/* Metadata chips */}
      <div className="flex flex-wrap gap-1.5">
        {profile.avg_age != null && (
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${chipClass}`}>
            {profile.avg_age.toFixed(0)} anos
          </span>
        )}
        {profile.avg_income != null && (
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${chipClass}`}>
            {formatCurrency(profile.avg_income)}
          </span>
        )}
        {profile.top_education && (
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${chipClass}`}>
            {profile.top_education}
          </span>
        )}
      </div>
    </div>
  );
}

export function SynthProfileAnalysis({ experimentId }: SynthProfileAnalysisProps) {
  const { data, isLoading } = useSynthProfiles(experimentId);

  if (isLoading) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 text-violet-500 mx-auto animate-spin" />
      </div>
    );
  }

  if (!data) return null;

  const clusterEntries = Object.entries(data.clusters).sort(
    (a, b) => b[1].avg_adoption - a[1].avg_adoption
  );

  const pieData = clusterEntries.map(([name, stats]) => ({
    name: CLUSTER_LABELS[name] ?? name,
    value: stats.count,
    adoption: stats.avg_adoption,
  }));

  const totalSynths = pieData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h3 className="text-base font-semibold text-slate-800 mb-1">Perfil dos Synths</h3>
        <p className="text-sm text-slate-500">
          Quem são os synths mais e menos propensos a adotar?{' '}
          <span className="font-medium text-slate-600">
            Melhor cenário: {data.best_scenario_mean.toFixed(1)}%
          </span>
        </p>
      </div>

      {/* Adopters vs Rejectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ProfileCard
          label="Propensos a adotar (top 20%)"
          icon={UserCheck}
          profile={data.adopters}
          variant="adopter"
        />
        <ProfileCard
          label="Resistentes (bottom 20%)"
          icon={UserX}
          profile={data.rejectors}
          variant="rejector"
        />
      </div>

      {/* Clusters — Donut + Legend */}
      {pieData.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-semibold text-slate-700 mb-4">Clusters Demográficos</p>

          <div className="flex items-center gap-6">
            {/* Donut */}
            <div className="h-56 w-56 shrink-0 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={68}
                    outerRadius={100}
                    dataKey="value"
                    paddingAngle={2}
                    isAnimationActive={false}
                  >
                    {pieData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                        stroke="white"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, _name: string, props: any) => [
                      `${value} synths · adoção ${props.payload.adoption.toFixed(1)}%`,
                      props.payload.name,
                    ]}
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 8,
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Center label */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <p className="text-2xl font-black text-slate-800">{totalSynths}</p>
                <p className="text-[10px] text-slate-400 uppercase tracking-wide">synths</p>
              </div>
            </div>

            {/* Legend */}
            <div className="flex-1 space-y-3">
              {pieData.map((item, i) => {
                const pct = totalSynths > 0 ? (item.value / totalSynths) * 100 : 0;
                const color = CLUSTER_COLORS[i % CLUSTER_COLORS.length];
                return (
                  <div key={item.name} className="flex items-center gap-3">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700 leading-tight">{item.name}</p>
                      <p className="text-xs text-slate-400">{item.value} synths · {pct.toFixed(0)}% do total</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold" style={{ color }}>
                        {item.adoption.toFixed(1)}%
                      </p>
                      <p className="text-[10px] text-slate-400">adoção</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
