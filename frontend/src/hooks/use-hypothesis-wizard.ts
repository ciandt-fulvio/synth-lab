/**
 * React Query hooks for hypothesis wizard operations.
 *
 * Provides hooks for simplified hypothesis generation via wizard flow.
 *
 * References:
 * - API: frontend/src/services/hypothesis-wizard-api.ts
 * - Spec: specs/036-simplified-hypothesis-wizard/spec.md
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  initWizard,
  applyClarifications,
  type WizardInitRequest,
  type WizardInitResponse,
  type WizardClarifyRequest,
  type WizardClarifyResponse,
} from '@/services/hypothesis-wizard-api';

/**
 * Hook to initialize hypothesis wizard with scenario profile.
 *
 * Generates baseline hypotheses for all DAG variables and returns
 * clarification questions for critical variables.
 *
 * @returns Mutation for initializing wizard
 *
 * @example
 * const { mutate: initialize } = useInitWizard();
 * initialize({
 *   simulationId: 'sim_12345678',
 *   request: { scenario_profile: 'realistic' }
 * });
 */
export function useInitWizard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: WizardInitRequest;
    }) => initWizard(simulationId, request),
    onSuccess: (data: WizardInitResponse, variables) => {
      // Invalidate hypotheses queries to reflect new wizard-generated hypotheses
      queryClient.invalidateQueries({
        queryKey: queryKeys.hypotheses.list(variables.simulationId),
      });

      // Update simulation detail (status might change)
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to apply clarification responses and refine hypotheses.
 *
 * Adjusts hypothesis parameters based on qualitative user feedback
 * (more/less/equal/dont_know) to critical variables.
 *
 * @returns Mutation for applying clarifications
 *
 * @example
 * const { mutate: clarify } = useApplyClarifications();
 * clarify({
 *   simulationId: 'sim_12345678',
 *   request: {
 *     responses: [
 *       { variable_name: 'Revenue', response: 'more' },
 *       { variable_name: 'Cost', response: 'less' }
 *     ]
 *   }
 * });
 */
export function useApplyClarifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: WizardClarifyRequest;
    }) => applyClarifications(simulationId, request),
    onSuccess: (data: WizardClarifyResponse, variables) => {
      // Invalidate hypotheses queries to reflect updated hypotheses
      queryClient.invalidateQueries({
        queryKey: queryKeys.hypotheses.list(variables.simulationId),
      });

      // Update simulation detail
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(variables.simulationId),
      });
    },
  });
}
