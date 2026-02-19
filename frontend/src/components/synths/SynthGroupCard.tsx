/**
 * SynthGroupCard component.
 *
 * Card display for a synth group. Navigates to the group detail page on click.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md (US2)
 *   - Types: src/types/synthGroup.ts
 */

import { useNavigate } from 'react-router-dom';
import { Users, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { SynthGroupSummary } from '@/types/synthGroup';

interface SynthGroupCardProps {
  group: SynthGroupSummary;
}

const FILL_REFERENCE = 1000;

export function SynthGroupCard({ group }: SynthGroupCardProps) {
  const navigate = useNavigate();
  const isDefault = group.id === 'grp_default';
  const fillPct = Math.min((group.synth_count / FILL_REFERENCE) * 100, 100);

  const formattedDate = formatDistanceToNow(new Date(group.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  return (
    <div
      onClick={() => navigate(`/synths/groups/${group.id}`)}
      className={`group relative cursor-pointer rounded-xl border bg-white pl-5 pr-5 py-5 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ${
        isDefault
          ? 'border-slate-200 hover:border-slate-300'
          : 'border-indigo-100 hover:border-indigo-200'
      }`}
    >
      {/* Left accent stripe */}
      <div
        className={`absolute left-0 top-4 bottom-4 w-[3px] rounded-full transition-colors duration-200 ${
          isDefault
            ? 'bg-slate-300 group-hover:bg-slate-400'
            : 'bg-gradient-to-b from-indigo-400 to-violet-500 group-hover:from-indigo-500 group-hover:to-violet-600'
        }`}
      />

      {/* Header: icon + name + description */}
      <div className="flex items-start gap-3 mb-4">
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center ${
            isDefault ? 'bg-slate-100 text-slate-500' : 'bg-indigo-50 text-indigo-600'
          }`}
        >
          <Users className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <h3 className="font-semibold text-sm text-slate-800 truncate leading-tight">
            {group.name}
          </h3>
          {group.description && (
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{group.description}</p>
          )}
        </div>
      </div>

      {/* Stat: synth count hero */}
      <div className="mb-3">
        <div className="flex items-baseline gap-1.5 mb-1.5">
          <span
            className={`text-2xl font-bold tabular-nums leading-none ${
              isDefault ? 'text-slate-700' : 'text-indigo-700'
            }`}
          >
            {group.synth_count.toLocaleString('pt-BR')}
          </span>
          <span className="text-xs text-slate-400 font-medium">participantes</span>
        </div>
        {/* Fill bar */}
        <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isDefault ? 'bg-slate-300' : 'bg-gradient-to-r from-indigo-400 to-violet-400'
            }`}
            style={{ width: `${fillPct}%` }}
          />
        </div>
      </div>

      {/* Footer: timestamp */}
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Clock className="h-3 w-3" />
        <span>{formattedDate}</span>
      </div>
    </div>
  );
}
