/**
 * Utility functions for exploration feature.
 *
 * Transforms API data to visualization format and provides formatting helpers.
 */

import type { ScenarioNode, TreeNodeData } from '@/types/exploration';

/**
 * Transform API nodes to react-d3-tree format.
 *
 * Builds a hierarchical tree structure from flat node array.
 *
 * @param nodes - Flat array of scenario nodes from API
 * @returns Root TreeNodeData or null if no root found
 */
export function transformToTreeData(nodes: ScenarioNode[]): TreeNodeData | null {
  if (!nodes || nodes.length === 0) return null;

  // Build parent-child map
  const nodeMap = new Map<string, ScenarioNode>();
  const childrenMap = new Map<string, string[]>();

  nodes.forEach((node) => {
    nodeMap.set(node.id, node);
    if (node.parent_id) {
      const siblings = childrenMap.get(node.parent_id) || [];
      siblings.push(node.id);
      childrenMap.set(node.parent_id, siblings);
    }
  });

  // Find root (parent_id === null)
  const root = nodes.find((n) => n.parent_id === null);
  if (!root) return null;

  // Recursive build
  function buildNode(nodeId: string): TreeNodeData {
    const node = nodeMap.get(nodeId)!;
    const childIds = childrenMap.get(nodeId) || [];

    return {
      name: node.simulation_results
        ? `${(node.simulation_results.success_rate * 100).toFixed(0)}%`
        : '—',
      attributes: {
        action: node.action_applied
          ? node.action_applied.slice(0, 30) + (node.action_applied.length > 30 ? '...' : '')
          : undefined,
        status: node.node_status,
      },
      children: childIds.length > 0 ? childIds.map(buildNode) : undefined,
      __nodeData: node,
    };
  }

  return buildNode(root.id);
}

/**
 * Get node IDs in the winning path.
 *
 * @param nodes - All nodes in the tree
 * @param winnerNodeId - ID of the winner node
 * @returns Set of node IDs in the winning path
 */
export function getWinningPathNodeIds(
  nodes: ScenarioNode[],
  winnerNodeId: string
): Set<string> {
  const pathIds = new Set<string>();
  const nodeMap = new Map<string, ScenarioNode>();

  nodes.forEach((node) => nodeMap.set(node.id, node));

  // Walk from winner to root
  let currentId: string | null = winnerNodeId;
  while (currentId) {
    pathIds.add(currentId);
    const current = nodeMap.get(currentId);
    currentId = current?.parent_id ?? null;
  }

  return pathIds;
}

/**
 * Format success rate as percentage.
 *
 * @param rate - Success rate as decimal (0-1) or null
 * @returns Formatted string like "25.5%" or "—" if null
 */
export function formatSuccessRate(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return '—';
  return `${(rate * 100).toFixed(1)}%`;
}

/**
 * Format delta with sign.
 *
 * @param delta - Delta value as decimal (can be negative)
 * @returns Formatted string like "+5.2%" or "-3.1%"
 */
export function formatDelta(delta: number): string {
  const sign = delta >= 0 ? '+' : '';
  return `${sign}${(delta * 100).toFixed(1)}%`;
}

/**
 * Format duration in seconds to human-readable string.
 *
 * @param seconds - Duration in seconds or null
 * @returns Formatted string like "2.5s" or "—" if null
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs.toFixed(0)}s`;
}

/**
 * Truncate text with ellipsis.
 *
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text with "..." if needed
 */
export function truncateText(text: string | null | undefined, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Get category display name in Portuguese.
 *
 * @param category - Category ID from API
 * @returns Human-readable category name
 */
export function getCategoryDisplayName(category: string | null | undefined): string {
  if (!category) return '—';

  const categoryMap: Record<string, string> = {
    ux_interface: 'UX / Interface',
    onboarding_education: 'Onboarding / Educação',
    flow_process: 'Fluxo / Processo',
    communication_feedback: 'Comunicação / Feedback',
    operational_feature_control: 'Operacional / Feature Control',
  };

  return categoryMap[category] || category;
}
