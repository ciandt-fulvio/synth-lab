// src/components/shared/ArtifactButton.tsx

import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { Eye, Loader2, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import type { ArtifactButtonProps, ArtifactStateEnum, ArtifactType } from '@/types/artifact-state';

/**
 * Configuration for each artifact state.
 */
interface StateConfig {
  label: string;
  icon: React.ReactNode;
  variant: 'default' | 'secondary' | 'outline' | 'destructive' | 'ghost';
  disabled: boolean;
}

/**
 * Get state-specific configuration for button display.
 */
function getStateConfig(
  state: ArtifactStateEnum,
  artifactType: ArtifactType,
  isPending: boolean = false
): StateConfig {
  const artifactLabel = artifactType === 'summary' ? 'Summary' : 'PR/FAQ';

  if (isPending) {
    return {
      label: `Gerando ${artifactLabel}...`,
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      variant: 'secondary',
      disabled: true,
    };
  }

  switch (state) {
    case 'available':
      return {
        label: `Visualizar ${artifactLabel}`,
        icon: <Eye className="h-4 w-4" />,
        variant: 'default',
        disabled: false,
      };

    case 'generating':
      return {
        label: `Gerando ${artifactLabel}...`,
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        variant: 'secondary',
        disabled: true,
      };

    case 'failed':
      return {
        label: `Tentar ${artifactLabel} novamente`,
        icon: <RefreshCw className="h-4 w-4" />,
        variant: 'destructive',
        disabled: false,
      };

    case 'unavailable':
    default:
      return {
        label: `Gerar ${artifactLabel}`,
        icon: <FileText className="h-4 w-4" />,
        variant: 'outline',
        disabled: false, // Will be controlled by prerequisiteMessage
      };
  }
}

/**
 * Button component for viewing/generating artifacts (Summary and PR-FAQ).
 *
 * Displays different states:
 * - Available: "Visualizar" button to open content
 * - Unavailable: Disabled or "Gerar" button depending on artifact type
 * - Generating: Loading spinner with "Gerando..."
 * - Failed: "Tentar novamente" with error tooltip
 */
export function ArtifactButton({
  state,
  artifactType,
  prerequisiteMessage,
  errorMessage,
  onGenerate,
  onView,
  onRetry,
  isPending = false,
  className,
}: ArtifactButtonProps) {
  const config = getStateConfig(state, artifactType, isPending);

  // Determine if button should be disabled
  const isDisabled = config.disabled || (state === 'unavailable' && !!prerequisiteMessage);

  // Handle click based on state
  const handleClick = () => {
    if (state === 'available') {
      onView();
    } else if (state === 'failed' && onRetry) {
      onRetry();
    } else if (state === 'unavailable' && onGenerate && !prerequisiteMessage) {
      onGenerate();
    }
  };

  const button = (
    <Button
      variant={config.variant}
      onClick={handleClick}
      disabled={isDisabled}
      className={cn(className)}
    >
      {config.icon}
      {config.label}
    </Button>
  );

  // Wrap with tooltip if there's a prerequisite message or error
  if (prerequisiteMessage || state === 'failed') {
    const tooltipMessage = state === 'failed'
      ? (errorMessage || 'A geracao falhou. Clique para tentar novamente.')
      : prerequisiteMessage;

    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className={isDisabled ? 'cursor-not-allowed' : undefined}>
              {button}
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <div className="flex items-center gap-2">
              {state === 'failed' && <AlertCircle className="h-4 w-4 text-destructive" />}
              <span>{tooltipMessage}</span>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return button;
}
