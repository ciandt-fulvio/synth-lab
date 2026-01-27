/**
 * React Query hooks for Causal DAG operations.
 *
 * Provides hooks for DAG CRUD, validation, and versioning with caching.
 *
 * References:
 *   - API: services/dag-api.ts
 *   - Types: types/causal-dag.ts
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  addEdge,
  addNode,
  compareDAGVersions,
  getDAG,
  listDAGVersions,
  removeEdge,
  removeNode,
  saveNodePositions,
  updateDAG,
  validateDAG,
} from '@/services/dag-api';
import type {
  CausalDAG,
  DAGCompareRequest,
  DAGUpdateRequest,
  DAGValidationRequest,
  Variable,
  Edge,
} from '@/types/causal-dag';

/**
 * Hook to fetch DAG for a simulation.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with DAG
 *
 * @example
 * const { data: dag } = useDAG("sim_123");
 */
export function useDAG(simulationId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.dag.detail(simulationId),
    queryFn: () => getDAG(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to update DAG structure.
 *
 * @returns Mutation for updating DAG
 *
 * @example
 * const { mutate: update } = useUpdateDAG();
 * update({ simulationId: "sim_123", request: { add_nodes: [...] } });
 */
export function useUpdateDAG() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: DAGUpdateRequest;
    }) => updateDAG(simulationId, request),
    onSuccess: (_, variables) => {
      // Invalidate DAG cache
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.detail(variables.simulationId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.versions(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to validate DAG structure.
 *
 * @returns Mutation for validating DAG
 *
 * @example
 * const { mutate: validate, data: result } = useValidateDAG();
 * validate({ simulationId: "sim_123", request: { nodes: [...], edges: [...] } });
 */
export function useValidateDAG() {
  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: DAGValidationRequest;
    }) => validateDAG(simulationId, request),
  });
}

/**
 * Hook to list DAG versions.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with version list
 *
 * @example
 * const { data: versions } = useDAGVersions("sim_123");
 */
export function useDAGVersions(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.dag.versions(simulationId),
    queryFn: () => listDAGVersions(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to compare DAG versions.
 *
 * @returns Mutation for comparing versions
 *
 * @example
 * const { mutate: compare, data: diff } = useCompareDAGVersions();
 * compare({ simulationId: "sim_123", request: { version_a: 1, version_b: 2 } });
 */
export function useCompareDAGVersions() {
  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: DAGCompareRequest;
    }) => compareDAGVersions(simulationId, request),
  });
}

/**
 * Hook to add a node to the DAG.
 *
 * @returns Mutation for adding node
 *
 * @example
 * const { mutate: add } = useAddNode();
 * add({ simulationId: "sim_123", node: { name: "x", label: "X", ... } });
 */
export function useAddNode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      node,
    }: {
      simulationId: string;
      node: Variable;
    }) => addNode(simulationId, node),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to remove a node from the DAG.
 *
 * @returns Mutation for removing node
 *
 * @example
 * const { mutate: remove } = useRemoveNode();
 * remove({ simulationId: "sim_123", nodeName: "x" });
 */
export function useRemoveNode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      nodeName,
    }: {
      simulationId: string;
      nodeName: string;
    }) => removeNode(simulationId, nodeName),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to add an edge to the DAG.
 *
 * @returns Mutation for adding edge
 *
 * @example
 * const { mutate: add } = useAddEdge();
 * add({ simulationId: "sim_123", edge: { source: "a", target: "b", ... } });
 */
export function useAddEdge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      edge,
    }: {
      simulationId: string;
      edge: Edge;
    }) => addEdge(simulationId, edge),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to remove an edge from the DAG.
 *
 * @returns Mutation for removing edge
 *
 * @example
 * const { mutate: remove } = useRemoveEdge();
 * remove({ simulationId: "sim_123", source: "a", target: "b" });
 */
export function useRemoveEdge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      source,
      target,
    }: {
      simulationId: string;
      source: string;
      target: string;
    }) => removeEdge(simulationId, source, target),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.dag.detail(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to save node positions.
 *
 * @returns Mutation for saving positions
 *
 * @example
 * const { mutate: save } = useSaveNodePositions();
 * save({ simulationId: "sim_123", positions: { "node1": {x: 100, y: 200} } });
 */
export function useSaveNodePositions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      positions,
    }: {
      simulationId: string;
      positions: Record<string, { x: number; y: number }>;
    }) => saveNodePositions(simulationId, positions),
    onSuccess: (_, variables) => {
      // Update cache optimistically without refetch
      queryClient.setQueryData(
        queryKeys.dag.detail(variables.simulationId),
        (old: CausalDAG | undefined) => {
          if (!old) return old;
          return {
            ...old,
            nodes: old.nodes.map((node) => {
              const pos = variables.positions[node.name];
              if (pos) {
                return { ...node, position_x: pos.x, position_y: pos.y };
              }
              return node;
            }),
          };
        }
      );
    },
  });
}

/**
 * Combined hook for DAG editor workflow.
 *
 * @param simulationId - Simulation ID
 * @returns All DAG operations and data
 *
 * @example
 * const { dag, addNode, removeNode, validate } = useDAGEditor("sim_123");
 */
export function useDAGEditor(simulationId: string) {
  const dagQuery = useDAG(simulationId);
  const versionsQuery = useDAGVersions(simulationId);
  const updateMutation = useUpdateDAG();
  const validateMutation = useValidateDAG();
  const addNodeMutation = useAddNode();
  const removeNodeMutation = useRemoveNode();
  const addEdgeMutation = useAddEdge();
  const removeEdgeMutation = useRemoveEdge();
  const compareMutation = useCompareDAGVersions();
  const savePositionsMutation = useSaveNodePositions();

  return {
    // Data
    dag: dagQuery.data,
    versions: versionsQuery.data,
    isLoading: dagQuery.isLoading,
    isLoadingVersions: versionsQuery.isLoading,
    error: dagQuery.error,

    // Mutations
    updateDAG: (request: DAGUpdateRequest) =>
      updateMutation.mutate({ simulationId, request }),
    validateDAG: (request: DAGValidationRequest) =>
      validateMutation.mutate({ simulationId, request }),
    addNode: (node: Variable) =>
      addNodeMutation.mutate({ simulationId, node }),
    removeNode: (nodeName: string) =>
      removeNodeMutation.mutate({ simulationId, nodeName }),
    addEdge: (edge: Edge) =>
      addEdgeMutation.mutate({ simulationId, edge }),
    removeEdge: (source: string, target: string) =>
      removeEdgeMutation.mutate({ simulationId, source, target }),
    compareVersions: (request: DAGCompareRequest) =>
      compareMutation.mutate({ simulationId, request }),
    savePositions: (positions: Record<string, { x: number; y: number }>) =>
      savePositionsMutation.mutate({ simulationId, positions }),

    // Mutation states
    isUpdating: updateMutation.isPending,
    isValidating: validateMutation.isPending,
    validationResult: validateMutation.data,
    comparisonResult: compareMutation.data,
  };
}
