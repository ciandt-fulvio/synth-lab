/**
 * ExperimentCard component (Refactored).
 *
 * Card display for an experiment in the list view.
 * Shows tags, activity indicators (interviews, materials, quanti, simulation),
 * and a 3-dot actions menu.
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 *   - Types: src/types/experiment.ts
 */

import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import {
  Calendar,
  MessageSquare,
  Loader2,
  Paperclip,
  BarChart3,
  Activity,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { ExperimentSummary } from '@/types/experiment';
import { ExperimentActionsMenu } from './ExperimentActionsMenu';

interface ExperimentCardProps {
  experiment: ExperimentSummary & { _isOptimistic?: boolean };
  onClick: (id: string) => void;
}

export function ExperimentCard({ experiment, onClick }: ExperimentCardProps) {
  const isOptimistic = experiment._isOptimistic;

  const displayDate = experiment.updated_at || experiment.created_at;
  const formattedDate = formatDistanceToNow(new Date(displayDate), {
    addSuffix: true,
    locale: ptBR,
  });

  // Truncate hypothesis to ~100 chars with ellipsis
  const truncatedHypothesis = experiment.hypothesis.length > 100
    ? `${experiment.hypothesis.slice(0, 97)}...`
    : experiment.hypothesis;

  return (
    <Card
      className={`transition-all duration-200 ${
        isOptimistic
          ? 'opacity-70 cursor-wait border-purple-300 bg-purple-50/50'
          : 'cursor-pointer hover:shadow-lg hover:border-purple-200'
      }`}
      onClick={() => !isOptimistic && onClick(experiment.id)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-1">
            {experiment.name}
          </CardTitle>
          {isOptimistic ? (
            <Badge variant="outline" className="text-purple-600 border-purple-300 text-xs">
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Criando...
            </Badge>
          ) : (
            <ExperimentActionsMenu
              experimentId={experiment.id}
              experimentName={experiment.name}
            />
          )}
        </div>
        <CardDescription className="text-sm text-gray-600 line-clamp-2 min-h-[2.5rem]">
          {truncatedHypothesis}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Tags */}
        {experiment.tags && experiment.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {experiment.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200"
              >
                {tag}
              </span>
            ))}
            {experiment.tags.length > 3 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                +{experiment.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Activity indicators + date */}
        <div className="flex items-center justify-between text-sm text-muted-foreground mt-2">
          <div className="flex items-center gap-3">
            {/* Quanti Analysis (tab 1) */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={`flex items-center gap-0.5 ${experiment.has_quanti ? 'text-violet-600' : 'text-slate-300'}`}>
                  <BarChart3 className="h-3.5 w-3.5" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{experiment.has_quanti ? 'Análise quanti realizada' : 'Sem análise quanti'}</p>
              </TooltipContent>
            </Tooltip>

            {/* Simulation (tab 2) */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={`flex items-center gap-0.5 ${experiment.has_simulation ? 'text-emerald-600' : 'text-slate-300'}`}>
                  <Activity className="h-3.5 w-3.5" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{experiment.has_simulation ? 'Simulação realizada' : 'Sem simulação'}</p>
              </TooltipContent>
            </Tooltip>

            {/* Interviews (tab 3) */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={`flex items-center gap-1 ${experiment.interview_count > 0 ? 'text-blue-600' : 'text-slate-300'}`}>
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span className="text-xs">{experiment.interview_count}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{experiment.interview_count} entrevista(s)</p>
              </TooltipContent>
            </Tooltip>

            {/* Materials (tab 4) */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={`flex items-center gap-1 ${experiment.materials_count > 0 ? 'text-amber-600' : 'text-slate-300'}`}>
                  <Paperclip className="h-3.5 w-3.5" />
                  <span className="text-xs">{experiment.materials_count}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{experiment.materials_count} material(is)</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-1 text-xs">
            <Calendar className="h-3 w-3" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
