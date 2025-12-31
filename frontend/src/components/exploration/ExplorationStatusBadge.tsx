/**
 * ExplorationStatusBadge component.
 *
 * Badge displaying exploration status with appropriate color and icon.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US5)
 */

import { Badge } from '@/components/ui/badge';
import {
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import type { ExplorationStatus } from '@/types/exploration';
import { EXPLORATION_STATUS_CONFIG } from '@/types/exploration';

interface ExplorationStatusBadgeProps {
  status: ExplorationStatus;
  className?: string;
}

const STATUS_ICONS: Record<string, React.ReactNode> = {
  Loader2: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
  CheckCircle: <CheckCircle className="h-3.5 w-3.5" />,
  AlertTriangle: <AlertTriangle className="h-3.5 w-3.5" />,
  XCircle: <XCircle className="h-3.5 w-3.5" />,
};

const VARIANT_CLASSES: Record<string, string> = {
  success: 'bg-green-100 text-green-800 border-green-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  neutral: 'bg-slate-100 text-slate-800 border-slate-200',
};

export function ExplorationStatusBadge({
  status,
  className = '',
}: ExplorationStatusBadgeProps) {
  const config = EXPLORATION_STATUS_CONFIG[status];
  const icon = STATUS_ICONS[config.icon];
  const variantClass = VARIANT_CLASSES[config.variant];

  return (
    <Badge
      variant="outline"
      className={`flex items-center gap-1.5 ${variantClass} ${className}`}
    >
      {icon}
      {config.label}
    </Badge>
  );
}
