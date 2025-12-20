// src/components/shared/StatusBadge.tsx

import { Badge } from '@/components/ui/badge';
import type { ExecutionStatus } from '@/types';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: ExecutionStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig: Record<
    ExecutionStatus,
    { label: string; className: string }
  > = {
    pending: {
      label: 'Pendente',
      className: 'bg-gray-100 text-gray-700 border-gray-300'
    },
    running: {
      label: 'Em Execução',
      className: 'bg-blue-100 text-blue-700 border-blue-300'
    },
    generating_summary: {
      label: 'Gerando Summary',
      className: 'bg-purple-100 text-purple-700 border-purple-300'
    },
    completed: {
      label: 'Concluída',
      className: 'bg-green-100 text-green-700 border-green-300'
    },
    failed: {
      label: 'Falhou',
      className: 'bg-red-100 text-red-700 border-red-300'
    },
  };

  const config = statusConfig[status];

  return (
    <Badge variant="outline" className={cn(config.className)}>
      {config.label}
    </Badge>
  );
}
