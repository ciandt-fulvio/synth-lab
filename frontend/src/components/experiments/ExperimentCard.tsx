/**
 * ExperimentCard component (Refactored).
 *
 * Card display for an experiment in the list view.
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 *   - Types: src/types/experiment.ts
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Calendar, FlaskConical, MessageSquare, CheckCircle, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { ExperimentSummary } from '@/types/experiment';

interface ExperimentCardProps {
  experiment: ExperimentSummary & { _isOptimistic?: boolean };
  onClick: (id: string) => void;
}

export function ExperimentCard({ experiment, onClick }: ExperimentCardProps) {
  const isOptimistic = experiment._isOptimistic;

  const formattedDate = formatDistanceToNow(new Date(experiment.created_at), {
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
          ) : null}
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
        <div className="flex items-center justify-between text-sm text-muted-foreground mt-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1" title="Análise Quantitativa">
              <FlaskConical className="h-4 w-4 text-purple-500" />
              {experiment.has_analysis ? (
                <CheckCircle className="h-3 w-3 text-green-500" />
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </div>
            <div className="flex items-center gap-1" title="Entrevistas">
              <MessageSquare className="h-4 w-4 text-blue-500" />
              <span>{experiment.interview_count}</span>
            </div>
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
