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
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { SynthGroupSummary } from '@/types/synthGroup';

interface SynthGroupCardProps {
  group: SynthGroupSummary;
}

export function SynthGroupCard({ group }: SynthGroupCardProps) {
  const navigate = useNavigate();

  const formattedDate = formatDistanceToNow(new Date(group.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  const isDefaultGroup = group.id === 'grp_default';
  const hasSynths = group.synth_count > 0;

  return (
    <Card
      className="cursor-pointer transition-all duration-200 h-full bg-gradient-to-br from-slate-50 to-white hover:shadow-lg hover:border-slate-300 hover:from-indigo-50/30 hover:to-white"
      onClick={() => navigate(`/synths/groups/${group.id}`)}
    >
      <CardHeader className="flex flex-col h-full gap-0 pb-4">
        <div className="flex items-start gap-3 mb-3">
          <div
            className={`flex-shrink-0 h-10 w-10 rounded-lg flex items-center justify-center ${
              isDefaultGroup
                ? 'bg-slate-200 text-slate-700'
                : 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white'
            }`}
          >
            <Users className="h-5 w-5" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg truncate">{group.name}</CardTitle>
              <Badge
                variant={hasSynths ? 'default' : 'secondary'}
                className={`flex-shrink-0 ${
                  hasSynths
                    ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {group.synth_count}
              </Badge>
            </div>
          </div>
        </div>

        <div className="min-h-[2.5rem] mb-3">
          {group.description && (
            <CardDescription className="line-clamp-2">{group.description}</CardDescription>
          )}
        </div>

        <div className="flex items-center pt-3 border-t border-slate-100 mt-auto">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
}
