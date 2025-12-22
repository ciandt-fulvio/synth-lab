/**
 * TypeScript type definitions for Summary and PR-FAQ State Management
 * Feature Branch: 013-summary-prfaq-states
 * Date: 2025-12-21
 *
 * These types should be added to frontend/src/types/
 */

// =============================================================================
// Enums
// =============================================================================

/**
 * Current state of an artifact (summary or PR-FAQ)
 */
export type ArtifactStateEnum = 'unavailable' | 'generating' | 'available' | 'failed';

/**
 * PR-FAQ generation status
 */
export type PRFAQStatus = 'generating' | 'completed' | 'failed';

// =============================================================================
// API Response Types
// =============================================================================

/**
 * State information for a single artifact
 */
export interface ArtifactState {
  /** Type of artifact */
  artifact_type: 'summary' | 'prfaq';
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
 * Request body for POST /prfaq/generate
 */
export interface PRFAQGenerateRequest {
  /** Research execution ID */
  exec_id: string;
  /** LLM model to use (default: gpt-4o-mini) */
  model?: string;
}

/**
 * Response from POST /prfaq/generate
 */
export interface PRFAQGenerateResponse {
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

// =============================================================================
// Component Props Types
// =============================================================================

/**
 * Props for the reusable ArtifactButton component
 */
export interface ArtifactButtonProps {
  /** Current state of the artifact */
  state: ArtifactStateEnum;
  /** Type of artifact */
  artifactType: 'summary' | 'prfaq';
  /** Message when prerequisite not met */
  prerequisiteMessage?: string;
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

// =============================================================================
// Hook Return Types
// =============================================================================

/**
 * Return type for useArtifactStates hook
 */
export interface UseArtifactStatesResult {
  /** Artifact states data */
  data: ArtifactStatesResponse | undefined;
  /** Whether data is loading */
  isLoading: boolean;
  /** Error if request failed */
  error: Error | null;
  /** Refetch function */
  refetch: () => void;
}

/**
 * Return type for usePrfaqGenerate hook
 */
export interface UsePrfaqGenerateResult {
  /** Mutation function to trigger generation */
  mutate: (request: PRFAQGenerateRequest) => void;
  /** Whether mutation is pending */
  isPending: boolean;
  /** Whether mutation succeeded */
  isSuccess: boolean;
  /** Whether mutation failed */
  isError: boolean;
  /** Error if mutation failed */
  error: Error | null;
  /** Response data if successful */
  data: PRFAQGenerateResponse | undefined;
}
