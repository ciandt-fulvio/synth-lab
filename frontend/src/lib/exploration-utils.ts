/**
 * Utility functions for exploration feature.
 *
 * Transforms API data to visualization format and provides formatting helpers.
 */

import dagre from 'dagrejs';
import type {
  ScenarioNode,
  TreeNodeData,
  DecisionNode,
  ExplorationEdge,
} from '@/types/exploration';

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
        shortAction: node.short_action ?? undefined,
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

// =============================================================================
// React Flow Layout (Preview)
// =============================================================================

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

/**
 * Build React Flow nodes and edges from API data using dagre layout.
 *
 * @param nodes - Flat array of scenario nodes from API
 * @param winnerNodeId - ID of the winner node for path highlighting
 * @returns Object with positioned nodes and styled edges
 */
export function buildReactFlowElements(
  nodes: ScenarioNode[],
  winnerNodeId: string | null
): { nodes: DecisionNode[]; edges: ExplorationEdge[] } {
  if (!nodes.length) return { nodes: [], edges: [] };

  // 1. Create dagre graph with horizontal (LR) layout
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 120 });
  g.setDefaultEdgeLabel(() => ({}));

  // 2. Add nodes and edges to dagre
  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    if (node.parent_id) {
      g.setEdge(node.parent_id, node.id);
    }
  });

  // 3. Calculate layout
  dagre.layout(g);

  // 4. Find the best node (highest success rate, excluding root)
  let bestNodeId: string | null = null;
  let bestSuccessRate = -1;
  nodes.forEach((node) => {
    if (node.parent_id === null) return; // Skip root
    const rate = node.simulation_results?.success_rate ?? -1;
    if (rate > bestSuccessRate) {
      bestSuccessRate = rate;
      bestNodeId = node.id;
    }
  });

  // 5. Calculate paths for highlighting
  // Priority: winner path (green) > best path (blue)
  const winningPath = winnerNodeId
    ? getWinningPathNodeIds(nodes, winnerNodeId)
    : new Set<string>();

  const bestPath =
    bestNodeId && !winnerNodeId
      ? getWinningPathNodeIds(nodes, bestNodeId)
      : new Set<string>();

  // Combined highlight path (winner takes precedence)
  const highlightPath = winningPath.size > 0 ? winningPath : bestPath;
  const isWinnerPath = winningPath.size > 0;

  // 6. Convert to React Flow nodes
  const flowNodes: DecisionNode[] = nodes.map((node) => {
    const pos = g.node(node.id);
    const isRoot = node.parent_id === null;
    const isWinner = node.node_status === 'winner';
    const isBest = node.id === bestNodeId && !isRoot;

    return {
      id: node.id,
      type: 'decision',
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
      data: {
        label: node.action_applied || 'Baseline',
        shortLabel: node.short_action,
        value: node.simulation_results
          ? node.simulation_results.success_rate * 100
          : null,
        status: node.node_status,
        isRoot,
        isBest,
        isWinner,
        originalNode: node,
      },
    };
  });

  // 7. Convert to React Flow edges with highlighted path
  const flowEdges: ExplorationEdge[] = nodes
    .filter((n) => n.parent_id)
    .map((node) => {
      const isOnHighlightPath =
        highlightPath.has(node.id) && highlightPath.has(node.parent_id!);

      // Different colors: green for winner, blue for best
      const highlightColor = isWinnerPath ? '#16a34a' : '#2563eb'; // green-600 or blue-600
      const highlightClass = isWinnerPath ? 'winning-path-edge' : 'best-path-edge';

      return {
        id: `e-${node.parent_id}-${node.id}`,
        source: node.parent_id!,
        target: node.id,
        type: 'smoothstep',
        animated: isOnHighlightPath,
        className: isOnHighlightPath ? highlightClass : '',
        style: isOnHighlightPath
          ? { stroke: highlightColor, strokeWidth: 4 }
          : { stroke: '#cbd5e1', strokeWidth: 2 },
      };
    });

  return { nodes: flowNodes, edges: flowEdges };
}
