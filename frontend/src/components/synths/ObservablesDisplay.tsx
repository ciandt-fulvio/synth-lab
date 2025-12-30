// src/components/synths/ObservablesDisplay.tsx

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import type { ObservableWithLabel, SimulationAttributesFormatted } from '@/types/synth';
import {
  getProgressBarClasses,
  getLabelBadgeClasses,
  formatValueAsPercentage,
} from '@/lib/observable-labels';

interface ObservablesDisplayProps {
  simulationAttributes?: SimulationAttributesFormatted;
}

/**
 * Component to display observable attributes for PM recruitment.
 *
 * Shows only observable characteristics (not latent traits) with:
 * - Name in Portuguese
 * - Numeric value as progress bar
 * - Textual label (Muito Baixo/Baixo/Médio/Alto/Muito Alto)
 * - Description tooltip
 *
 * Reference: specs/022-observable-latent-traits/spec.md (US1, US4)
 */
export function ObservablesDisplay({ simulationAttributes }: ObservablesDisplayProps) {
  const observables = simulationAttributes?.observables_formatted ?? [];

  if (observables.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Capacidades</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Informações de capacidades não disponíveis para este synth.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Capacidades
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>
                  Características observáveis que podem ser identificadas em pessoas reais
                  para recrutamento de participantes equivalentes.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {observables.map((observable) => (
          <ObservableItem key={observable.key} observable={observable} />
        ))}
      </CardContent>
    </Card>
  );
}

interface ObservableItemProps {
  observable: ObservableWithLabel;
}

function ObservableItem({ observable }: ObservableItemProps) {
  const progressClasses = getProgressBarClasses(observable);
  const badgeClasses = getLabelBadgeClasses(observable);
  const percentage = observable.value * 100;

  return (
    <div className="space-y-2">
      {/* Header: Name + Label + Tooltip */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{observable.name}</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-3.5 w-3.5 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{observable.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {formatValueAsPercentage(observable.value)}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${badgeClasses}`}
          >
            {observable.label}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className={`h-2 rounded-full ${progressClasses.background}`}>
        <div
          className={`h-full rounded-full transition-all ${progressClasses.fill}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
