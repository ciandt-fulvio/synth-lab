/**
 * API client for exploration feature.
 *
 * Consumes endpoints from backend spec 024.
 * See: specs/025-exploration-frontend/contracts/api-client.md
 */

import { fetchAPI } from './api';
import type {
  Exploration,
  ExplorationCreate,
  ExplorationTree,
  WinningPath,
  ActionCatalog,
  ExplorationSummary,
} from '@/types/exploration';

/**
 * Create a new exploration for an experiment.
 *
 * @param data - Exploration creation parameters
 * @returns Created exploration
 * @throws APIError if experiment not found or no baseline analysis
 */
export async function createExploration(data: ExplorationCreate): Promise<Exploration> {
  return fetchAPI<Exploration>('/explorations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get an exploration by ID.
 *
 * @param id - Exploration ID (expl_xxxxxxxx)
 * @returns Exploration data
 * @throws APIError if not found
 */
export async function getExploration(id: string): Promise<Exploration> {
  return fetchAPI<Exploration>(`/explorations/${id}`);
}

/**
 * Start running an exploration in background.
 *
 * @param id - Exploration ID
 * @returns Current exploration state (will update in background)
 */
export async function runExploration(id: string): Promise<Exploration> {
  return fetchAPI<Exploration>(`/explorations/${id}/run`, {
    method: 'POST',
  });
}

/**
 * Get the complete exploration tree with all nodes.
 *
 * @param id - Exploration ID
 * @returns Tree structure with nodes and status counts
 */
export async function getExplorationTree(id: string): Promise<ExplorationTree> {
  return fetchAPI<ExplorationTree>(`/explorations/${id}/tree`);
}

/**
 * Get the winning path if exploration achieved goal.
 *
 * @param id - Exploration ID
 * @returns Winning path or null if no winner
 */
export async function getWinningPath(id: string): Promise<WinningPath | null> {
  return fetchAPI<WinningPath | null>(`/explorations/${id}/winning-path`);
}

/**
 * Get the action catalog with all categories and examples.
 *
 * @returns Action catalog
 */
export async function getActionCatalog(): Promise<ActionCatalog> {
  return fetchAPI<ActionCatalog>('/explorations/catalog/actions');
}

/**
 * List explorations for an experiment.
 *
 * @param experimentId - Experiment ID
 * @returns List of exploration summaries
 */
export async function listExplorations(experimentId: string): Promise<ExplorationSummary[]> {
  return fetchAPI<ExplorationSummary[]>(`/experiments/${experimentId}/explorations`);
}
