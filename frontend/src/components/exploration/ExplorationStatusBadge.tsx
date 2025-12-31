/**
 * ExplorationStatusBadge component.
 *
 * Badge displaying exploration status with appropriate color and icon.
 * Uses the shared StatusBadge component for consistency.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US5)
 */

import {
  StatusBadge,
  EXPLORATION_STATUS_CONFIG,
} from '@/components/shared/StatusBadge';
import type { ExplorationStatus } from '@/types/exploration';

interface ExplorationStatusBadgeProps {
  status: ExplorationStatus;
  className?: string;
}

export function ExplorationStatusBadge({
  status,
  className,
}: ExplorationStatusBadgeProps) {
  return (
    <StatusBadge
      status={status}
      config={EXPLORATION_STATUS_CONFIG}
      className={className}
    />
  );
}
