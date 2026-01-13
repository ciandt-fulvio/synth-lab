/**
 * T025 SynthGroupCard component.
 *
 * Card display for a synth group in the list view.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md (US2)
 *   - Types: src/types/synthGroup.ts
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users, Calendar, Eye } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { SynthGroupSummary } from '@/types/synthGroup';

interface SynthGroupCardProps {
  group: SynthGroupSummary;
  onClick: (groupId: string) => void;
  onViewDetails?: (groupId: string) => void;
  isSelected?: boolean;
}

export function SynthGroupCard({
  group,
  onClick,
  onViewDetails,
  isSelected = false,
}: SynthGroupCardProps) {
  const formattedDate = formatDistanceToNow(new Date(group.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  const isDefaultGroup = group.id === 'grp_default';
  const hasSynths = group.synth_count > 0;

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 h-full ${
        isSelected
          ? 'border-indigo-600 border-2 shadow-xl bg-gradient-to-br from-indigo-50 via-violet-50 to-white'
          : 'bg-gradient-to-br from-slate-50 to-white hover:shadow-lg hover:border-slate-300 hover:from-indigo-50/30 hover:to-white'
      }`}
      onClick={() => onClick(group.id)}
    >
      <CardHeader className="flex flex-col h-full gap-0 pb-4">
        <div className="flex items-start gap-3 mb-3">
          {/* Ícone compacto */}
          <div
            className={`flex-shrink-0 h-10 w-10 rounded-lg flex items-center justify-center ${
              isDefaultGroup
                ? 'bg-slate-200 text-slate-700'
                : 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white'
            }`}
          >
            <Users className="h-5 w-5" />
          </div>

          {/* Título e Badge */}
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

        {/* Descrição com altura fixa */}
        <div className="min-h-[2.5rem] mb-3">
          {group.description && (
            <CardDescription className="line-clamp-2">{group.description}</CardDescription>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100 mt-auto">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            <span>{formattedDate}</span>
          </div>

          {onViewDetails && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-3 text-xs border-slate-300 bg-white text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onViewDetails(group.id);
              }}
              aria-label={`Ver detalhes de ${group.name}`}
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              Detalhes
            </Button>
          )}
        </div>
      </CardHeader>
    </Card>
  );
}
