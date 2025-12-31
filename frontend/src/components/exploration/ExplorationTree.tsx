/**
 * ExplorationTree component.
 *
 * Interactive tree visualization with zoom/pan using react-d3-tree.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US2)
 *   - Library: https://bkrem.github.io/react-d3-tree/docs/
 */

import { useCallback, useMemo, useRef, useState, useEffect } from 'react';
import Tree from 'react-d3-tree';
import type { RawNodeDatum, CustomNodeElementProps } from 'react-d3-tree';
import { transformToTreeData, getWinningPathNodeIds } from '@/lib/exploration-utils';
import { CustomTreeNode } from './CustomTreeNode';
import type { ScenarioNode, TreeNodeData } from '@/types/exploration';
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ExplorationTreeProps {
  /** Array of scenario nodes from API */
  nodes: ScenarioNode[];
  /** Callback when a node is clicked */
  onNodeClick?: (node: ScenarioNode) => void;
  /** Currently selected node ID */
  selectedNodeId?: string | null;
  /** Winner node ID for path highlighting */
  winnerNodeId?: string | null;
  /** Optional className for container */
  className?: string;
}

// Tree configuration (adjusted for HTML card nodes)
const TREE_CONFIG = {
  nodeSize: { x: 180, y: 120 }, // More space for card-based nodes
  separation: { siblings: 1.4, nonSiblings: 1.6 }, // Better spacing
  zoom: 0.75,
  scaleExtent: { min: 0.5, max: 1.5 }, // More controlled zoom range
  translate: { x: 0, y: 60 },
};

export function ExplorationTree({
  nodes,
  onNodeClick,
  selectedNodeId,
  winnerNodeId,
  className = '',
}: ExplorationTreeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [zoom, setZoom] = useState(TREE_CONFIG.zoom);
  const [translate, setTranslate] = useState(TREE_CONFIG.translate);

  // Transform nodes to tree data format
  const treeData = useMemo(() => {
    const data = transformToTreeData(nodes);
    return data as RawNodeDatum | null;
  }, [nodes]);

  // Get winning path node IDs for highlighting
  const winningPathNodeIds = useMemo(() => {
    if (!winnerNodeId) return new Set<string>();
    return getWinningPathNodeIds(nodes, winnerNodeId);
  }, [nodes, winnerNodeId]);

  // Find the best node (highest success rate, excluding winner)
  const bestNodeId = useMemo(() => {
    if (!nodes.length) return null;

    let bestNode: ScenarioNode | null = null;
    let bestRate = -1;

    for (const node of nodes) {
      // Skip winner nodes and nodes without simulation results
      if (node.node_status === 'winner' || !node.simulation_results) continue;

      const rate = node.simulation_results.success_rate;
      if (rate > bestRate) {
        bestRate = rate;
        bestNode = node;
      }
    }

    return bestNode?.id ?? null;
  }, [nodes]);

  // Update dimensions when container resizes
  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
        // Center horizontally, position root at top
        setTranslate({ x: width / 2, y: TREE_CONFIG.translate.y });
      }
    };

    updateDimensions();

    const resizeObserver = new ResizeObserver(updateDimensions);
    resizeObserver.observe(containerRef.current);

    return () => resizeObserver.disconnect();
  }, []);

  // Custom node renderer
  const renderCustomNode = useCallback(
    (props: CustomNodeElementProps) => (
      <CustomTreeNode
        {...props}
        nodeDatum={props.nodeDatum as TreeNodeData}
        onNodeClick={onNodeClick}
        selectedNodeId={selectedNodeId}
        winningPathNodeIds={winningPathNodeIds}
        bestNodeId={bestNodeId}
      />
    ),
    [onNodeClick, selectedNodeId, winningPathNodeIds, bestNodeId]
  );

  // Zoom controls
  const handleZoomIn = () =>
    setZoom((z) => Math.min(z + 0.15, TREE_CONFIG.scaleExtent.max));
  const handleZoomOut = () =>
    setZoom((z) => Math.max(z - 0.15, TREE_CONFIG.scaleExtent.min));
  const handleReset = () => {
    setZoom(TREE_CONFIG.zoom);
    setTranslate({ x: dimensions.width / 2, y: TREE_CONFIG.translate.y });
  };
  const handleFit = () => {
    // Fit the tree to the container
    const nodeCount = nodes.length;
    const { min, max } = TREE_CONFIG.scaleExtent;
    const optimalZoom = Math.max(min, Math.min(max, 8 / nodeCount));
    setZoom(optimalZoom);
    setTranslate({ x: dimensions.width / 2, y: TREE_CONFIG.translate.y });
  };

  if (!treeData) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <p className="text-muted-foreground">Nenhum nó na árvore</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 bg-white/90"
          onClick={handleZoomIn}
          title="Aumentar zoom"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 bg-white/90"
          onClick={handleZoomOut}
          title="Diminuir zoom"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 bg-white/90"
          onClick={handleFit}
          title="Ajustar à tela"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 bg-white/90"
          onClick={handleReset}
          title="Resetar posição"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>

      {/* Tree Container */}
      <div
        ref={containerRef}
        className="w-full h-[500px] bg-slate-50 rounded-lg border"
      >
        <Tree
          data={treeData}
          orientation="vertical"
          pathFunc="step"
          translate={translate}
          zoom={zoom}
          scaleExtent={TREE_CONFIG.scaleExtent}
          nodeSize={TREE_CONFIG.nodeSize}
          separation={TREE_CONFIG.separation}
          renderCustomNodeElement={renderCustomNode}
          onUpdate={({ zoom: newZoom, translate: newTranslate }) => {
            setZoom(newZoom);
            setTranslate(newTranslate);
          }}
          enableLegacyTransitions
          transitionDuration={300}
          pathClassFunc={() =>
            winningPathNodeIds.size > 0
              ? 'stroke-amber-400 stroke-2'
              : 'stroke-slate-300'
          }
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-2 border-green-500 bg-green-50" />
          <span>Vencedor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-[3px] border-amber-500 bg-blue-50" />
          <span>Melhor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-2 border-blue-500 bg-blue-50" />
          <span>Ativo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-2 border-slate-300 bg-slate-50" />
          <span>Dominado</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-2 border-red-400 bg-red-50" />
          <span>Falhou</span>
        </div>
      </div>
    </div>
  );
}
