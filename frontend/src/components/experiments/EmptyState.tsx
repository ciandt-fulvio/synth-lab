/**
 * T023 EmptyState component.
 *
 * Empty state display when no experiments exist.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US1 Scenario 2)
 */

import { Button } from '@/components/ui/button';
import { FlaskConical, Plus } from 'lucide-react';

interface EmptyStateProps {
  onCreateClick: () => void;
}

export function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
        <FlaskConical className="w-8 h-8 text-primary" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        Nenhum experimento ainda
      </h3>
      <p className="text-gray-600 text-center max-w-md mb-6">
        Experimentos são o ponto de partida para testar suas hipóteses.
        Crie seu primeiro experimento para começar a explorar insights com personas sintéticas.
      </p>
      <Button onClick={onCreateClick}>
        <Plus className="w-4 h-4 mr-2" />
        Criar primeiro experimento
      </Button>
    </div>
  );
}
