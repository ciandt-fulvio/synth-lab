/**
 * StatusBadge - Unified status badge component.
 *
 * Generic badge for displaying status with optional icons and animations.
 * Used across the system for consistent status visualization.
 *
 * Usage:
 *   <StatusBadge status="running" config={EXECUTION_STATUS_CONFIG} />
 *   <StatusBadge status="completed" config={EXPLORATION_STATUS_CONFIG} />
 */

import { Badge } from '@/components/ui/badge';
import {
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// =============================================================================
// Types
// =============================================================================

export type BadgeVariant = 'success' | 'info' | 'warning' | 'error' | 'neutral';

export interface StatusConfig {
  label: string;
  variant: BadgeVariant;
  icon?: string; // Lucide icon name
}

export type StatusConfigMap<T extends string> = Record<T, StatusConfig>;

interface StatusBadgeProps<T extends string> {
  status: T;
  config: StatusConfigMap<T>;
  className?: string;
  showIcon?: boolean;
}

// =============================================================================
// Icon Registry
// =============================================================================

const ICON_REGISTRY: Record<string, LucideIcon> = {
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
};

// =============================================================================
// Variant Styles
// =============================================================================

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: 'bg-green-100 text-green-800 border-green-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  neutral: 'bg-slate-100 text-slate-800 border-slate-200',
};

// =============================================================================
// Predefined Configs
// =============================================================================

/**
 * Status config for research executions (interviews).
 */
export const EXECUTION_STATUS_CONFIG: StatusConfigMap<
  'pending' | 'running' | 'generating_summary' | 'completed' | 'failed'
> = {
  pending: { label: 'Pendente', variant: 'neutral', icon: 'Clock' },
  running: { label: 'Executando', variant: 'info', icon: 'Loader2' },
  generating_summary: { label: 'Gerando Resumo', variant: 'info', icon: 'FileText' },
  completed: { label: 'Concluída', variant: 'success', icon: 'CheckCircle' },
  failed: { label: 'Falhou', variant: 'error', icon: 'XCircle' },
};

/**
 * Status config for explorations.
 */
export const EXPLORATION_STATUS_CONFIG: StatusConfigMap<
  'running' | 'goal_achieved' | 'depth_limit_reached' | 'cost_limit_reached' | 'no_viable_paths'
> = {
  running: { label: 'Executando', variant: 'info', icon: 'Loader2' },
  goal_achieved: { label: 'Meta Atingida', variant: 'success', icon: 'CheckCircle' },
  depth_limit_reached: { label: 'Limite Profundidade', variant: 'warning', icon: 'AlertTriangle' },
  cost_limit_reached: { label: 'Limite Custo', variant: 'warning', icon: 'AlertTriangle' },
  no_viable_paths: { label: 'Sem Caminhos', variant: 'error', icon: 'XCircle' },
};

/**
 * Status config for scenario nodes.
 */
export const NODE_STATUS_CONFIG: StatusConfigMap<
  'active' | 'dominated' | 'winner' | 'expansion_failed'
> = {
  winner: { label: 'Vencedor', variant: 'success', icon: 'CheckCircle' },
  active: { label: 'Ativo', variant: 'info' },
  dominated: { label: 'Dominado', variant: 'neutral' },
  expansion_failed: { label: 'Falhou', variant: 'error', icon: 'XCircle' },
};

// =============================================================================
// Component
// =============================================================================

export function StatusBadge<T extends string>({
  status,
  config,
  className,
  showIcon = true,
}: StatusBadgeProps<T>) {
  const statusConfig = config[status];

  if (!statusConfig) {
    return (
      <Badge variant="outline" className={cn('bg-slate-100 text-slate-800', className)}>
        {status}
      </Badge>
    );
  }

  const { label, variant, icon } = statusConfig;
  const variantClass = VARIANT_CLASSES[variant];

  // Get icon component
  const IconComponent = icon ? ICON_REGISTRY[icon] : null;
  const isSpinner = icon === 'Loader2';

  return (
    <Badge
      variant="outline"
      className={cn('flex items-center gap-1.5', variantClass, className)}
    >
      {showIcon && IconComponent && (
        <IconComponent
          className={cn('h-3.5 w-3.5', isSpinner && 'animate-spin')}
        />
      )}
      {label}
    </Badge>
  );
}

// =============================================================================
// Legacy Support (backward compatibility)
// =============================================================================

import type { ExecutionStatus } from '@/types';

interface LegacyStatusBadgeProps {
  status: ExecutionStatus;
  className?: string;
}

/**
 * @deprecated Use StatusBadge with config instead.
 * Kept for backward compatibility.
 */
export function ExecutionStatusBadge({ status, className }: LegacyStatusBadgeProps) {
  return (
    <StatusBadge
      status={status}
      config={EXECUTION_STATUS_CONFIG}
      className={className}
    />
  );
}
