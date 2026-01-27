/**
 * React Query hooks for causal simulation operations.
 *
 * Provides hooks for simulation lifecycle management with caching and optimistic updates.
 *
 * References:
 *   - API: frontend/src/services/simulations-api.ts
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  confirmDAG,
  confirmHypotheses,
  confirmQuestion,
  createSimulation,
  deleteSimulation,
  exportSimulationAudit,
  getInsightTrace,
  getSimulation,
  getSimulationAudit,
  getSimulationInsights,
  listSimulations,
  replaySimulation,
  runSimulation,
  updateProblemDecomposition,
  type AuditTrailResponse,
  type ExportResponse,
  type InsightResponse,
  type InsightTraceResponse,
  type ProblemDecompositionUpdate,
  type ReplayResponse,
  type SimulationCreateRequest,
  type SimulationResponse,
  type SimulationRunRequest,
  type SimulationRunResponse,
  type SimulationStatus,
} from '@/services/simulations-api';

/**
 * Hook to create a new simulation from a question.
 *
 * @returns Mutation for creating simulation
 *
 * @example
 * const { mutate: create } = useCreateSimulation();
 * create({ question_text: "What will be the adoption rate?" });
 */
export function useCreateSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SimulationCreateRequest) => createSimulation(request),
    onSuccess: () => {
      // Invalidate simulations list
      queryClient.invalidateQueries({ queryKey: queryKeys.simulations.list() });
    },
  });
}

/**
 * Hook to run an existing simulation.
 *
 * @returns Mutation for running simulation
 *
 * @example
 * const { mutate: run } = useRunSimulation();
 * run({ simulationId: "sim_123", request: { n_worlds: 1000 } });
 */
export function useRunSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request?: SimulationRunRequest;
    }) => runSimulation(simulationId, request),
    onSuccess: (_, variables) => {
      // Invalidate simulation details and insights
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(variables.simulationId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.insights(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to delete a simulation.
 *
 * @returns Mutation for deleting simulation
 *
 * @example
 * const { mutate: remove } = useDeleteSimulation();
 * remove("sim_123");
 */
export function useDeleteSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (simulationId: string) => deleteSimulation(simulationId),
    onSuccess: () => {
      // Invalidate simulations list
      queryClient.invalidateQueries({ queryKey: queryKeys.simulations.list() });
    },
  });
}

// =============================================================================
// Wizard Flow Hooks
// =============================================================================

/**
 * Hook to update problem decomposition.
 *
 * @returns Mutation for updating problem decomposition
 *
 * @example
 * const { mutate: update } = useUpdateProblemDecomposition();
 * update({ simulationId: "sim_123", update: { intervention: "New text" } });
 */
export function useUpdateProblemDecomposition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      update,
    }: {
      simulationId: string;
      update: ProblemDecompositionUpdate;
    }) => updateProblemDecomposition(simulationId, update),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to confirm question and generate DAG.
 *
 * @returns Mutation for confirming question
 *
 * @example
 * const { mutate: confirm } = useConfirmQuestion();
 * confirm("sim_123");
 */
export function useConfirmQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (simulationId: string) => confirmQuestion(simulationId),
    onSuccess: (_, simulationId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(simulationId),
      });
    },
  });
}

/**
 * Hook to confirm DAG and generate hypotheses.
 *
 * @returns Mutation for confirming DAG
 *
 * @example
 * const { mutate: confirm } = useConfirmDAG();
 * confirm("sim_123");
 */
export function useConfirmDAG() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (simulationId: string) => confirmDAG(simulationId),
    onSuccess: (_, simulationId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(simulationId),
      });
    },
  });
}

/**
 * Hook to confirm hypotheses and mark ready to run.
 *
 * @returns Mutation for confirming hypotheses
 *
 * @example
 * const { mutate: confirm } = useConfirmHypotheses();
 * confirm("sim_123");
 */
export function useConfirmHypotheses() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (simulationId: string) => confirmHypotheses(simulationId),
    onSuccess: (_, simulationId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(simulationId),
      });
    },
  });
}

/**
 * Hook to fetch simulation details.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with simulation details
 *
 * @example
 * const { data: simulation } = useSimulation("sim_123");
 */
export function useSimulation(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.detail(simulationId),
    queryFn: () => getSimulation(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to list simulations with optional filtering.
 *
 * @param options - Filter options
 * @returns Query result with simulations list
 *
 * @example
 * const { data: simulations } = useSimulations({ status: 'completed' });
 */
export function useSimulations(options?: {
  status?: SimulationStatus;
  limit?: number;
}) {
  return useQuery({
    queryKey: queryKeys.simulations.list(options),
    queryFn: () => listSimulations(options),
  });
}

/**
 * Hook to fetch insights for a simulation.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with insights list
 *
 * @example
 * const { data: insights } = useSimulationInsights("sim_123");
 */
export function useSimulationInsights(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.insights(simulationId),
    queryFn: () => getSimulationInsights(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to fetch traceability details for an insight.
 *
 * @param insightId - Insight ID
 * @param options - Query options
 * @returns Query result with traceability details
 *
 * @example
 * const { data: trace } = useInsightTrace("ins_123");
 */
export function useInsightTrace(
  insightId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.insightTrace(insightId),
    queryFn: () => getInsightTrace(insightId),
    enabled: options?.enabled,
  });
}

/**
 * Combined hook for full simulation workflow.
 *
 * Provides all necessary operations for the simulation lifecycle.
 *
 * @returns Object with all simulation operations
 *
 * @example
 * const { createSimulation, runSimulation, simulation, insights } = useSimulationWorkflow("sim_123");
 */
export function useSimulationWorkflow(simulationId?: string) {
  const createMutation = useCreateSimulation();
  const runMutation = useRunSimulation();
  const deleteMutation = useDeleteSimulation();

  const simulationQuery = useSimulation(simulationId || '', {
    enabled: !!simulationId,
  });

  const insightsQuery = useSimulationInsights(simulationId || '', {
    enabled: !!simulationId,
  });

  return {
    // Mutations
    createSimulation: createMutation.mutate,
    runSimulation: (request?: SimulationRunRequest) =>
      simulationId && runMutation.mutate({ simulationId, request }),
    deleteSimulation: () => simulationId && deleteMutation.mutate(simulationId),

    // Mutation states
    isCreating: createMutation.isPending,
    isRunning: runMutation.isPending,
    isDeleting: deleteMutation.isPending,
    createError: createMutation.error,
    runError: runMutation.error,
    deleteError: deleteMutation.error,

    // Query data
    simulation: simulationQuery.data,
    insights: insightsQuery.data,
    isLoadingSimulation: simulationQuery.isLoading,
    isLoadingInsights: insightsQuery.isLoading,
    simulationError: simulationQuery.error,
    insightsError: insightsQuery.error,

    // Run result from mutation
    runResult: runMutation.data,
  };
}

/**
 * Hook to fetch audit trail for a simulation.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with audit trail
 *
 * @example
 * const { data: audit } = useSimulationAudit("sim_123");
 */
export function useSimulationAudit(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.audit(simulationId),
    queryFn: () => getSimulationAudit(simulationId),
    enabled: options?.enabled !== false && !!simulationId,
  });
}

/**
 * Hook to replay a simulation using stored audit trail.
 *
 * @returns Mutation for replaying simulation
 *
 * @example
 * const { mutate: replay } = useReplaySimulation();
 * replay("sim_123");
 */
export function useReplaySimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (simulationId: string) => replaySimulation(simulationId),
    onSuccess: (_, simulationId) => {
      // Invalidate simulation details and evidence
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.detail(simulationId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.evidence(simulationId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.simulations.insights(simulationId),
      });
    },
  });
}

/**
 * Hook to export audit trail as a portable package.
 *
 * @returns Mutation for exporting audit trail
 *
 * @example
 * const { mutate: exportAudit } = useExportAudit();
 * exportAudit("sim_123");
 */
export function useExportAudit() {
  return useMutation({
    mutationFn: (simulationId: string) => exportSimulationAudit(simulationId),
  });
}
