// src/components/shared/StatusBadge.tsx

import { Badge } from '@/components/ui/badge';
import type { ExecutionStatus } from '@/types';

interface StatusBadgeProps {
  status: ExecutionStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig: Record<
    ExecutionStatus,
    { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
  > = {
    pending: { label: 'Pendente', variant: 'outline' },
    running: { label: 'Em Execução', variant: 'default' },
    generating_summary: { label: 'Gerando Summary', variant: 'secondary' },
    completed: { label: 'Concluída', variant: 'secondary' },
    failed: { label: 'Falhou', variant: 'destructive' },
  };

  const config = statusConfig[status];

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
