// src/types/artifact-state.ts
// TypeScript type definitions for Summary and PR-FAQ State Management

/**
 * Current state of an artifact (summary or PR-FAQ)
 */
export type ArtifactStateEnum = 'unavailable' | 'generating' | 'available' | 'failed';

/**
 * Type of artifact
 */
export type ArtifactType = 'summary' | 'prfaq';

/**
 * PR-FAQ generation status
 */
export type PRFAQStatus = 'generating' | 'completed' | 'failed';

/**
 * State information for a single artifact
 */
export interface ArtifactState {
  /** Type of artifact */
  artifact_type: ArtifactType;
  /** Current state */
  state: ArtifactStateEnum;
  /** Whether generate action is available */
  can_generate: boolean;
  /** Whether view action is available */
  can_view: boolean;
  /** Whether prerequisites are satisfied */
  prerequisite_met: boolean;
  /** Message if prerequisite not met */
  prerequisite_message?: string | null;
  /** Last error message if failed */
  error_message?: string | null;
  /** Generation start timestamp */
  started_at?: string | null;
  /** Generation completion timestamp */
  completed_at?: string | null;
}

/**
 * Response from GET /research/{exec_id}/artifacts
 */
export interface ArtifactStatesResponse {
  /** Research execution ID */
  exec_id: string;
  /** Summary artifact state */
  summary: ArtifactState;
  /** PR-FAQ artifact state */
  prfaq: ArtifactState;
}

/**
 * Request body for POST /prfaq/generate (extended for state tracking)
 */
export interface PRFAQGenerateRequestWithState {
  /** Research execution ID */
  exec_id: string;
  /** LLM model to use (default: gpt-4o-mini) */
  model?: string;
}

/**
 * Response from POST /prfaq/generate (extended with state info)
 */
export interface PRFAQGenerateResponseWithState {
  /** Research execution ID */
  exec_id: string;
  /** Current generation status */
  status: PRFAQStatus;
  /** Status message */
  message?: string;
  /** Completion timestamp if completed */
  generated_at?: string | null;
  /** Error message if failed */
  error_message?: string | null;
}

/**
 * Props for the reusable ArtifactButton component
 */
export interface ArtifactButtonProps {
  /** Current state of the artifact */
  state: ArtifactStateEnum;
  /** Type of artifact */
  artifactType: ArtifactType;
  /** Message when prerequisite not met */
  prerequisiteMessage?: string;
  /** Error message when state is failed */
  errorMessage?: string;
  /** Callback when generate is clicked */
  onGenerate?: () => void;
  /** Callback when view is clicked */
  onView: () => void;
  /** Callback when retry is clicked (for failed state) */
  onRetry?: () => void;
  /** Whether generate/retry action is pending */
  isPending?: boolean;
  /** Custom class name */
  className?: string;
}
