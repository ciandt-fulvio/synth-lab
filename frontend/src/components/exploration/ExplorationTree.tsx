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

// Tree configuration
const TREE_CONFIG = {
  nodeSize: { x: 160, y: 100 },
  separation: { siblings: 1.2, nonSiblings: 1.5 },
  zoom: 0.8,
  translate: { x: 0, y: 50 },
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

  // Update dimensions when container resizes
  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
        // Center horizontally
        setTranslate({ x: width / 2, y: 50 });
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
      />
    ),
    [onNodeClick, selectedNodeId, winningPathNodeIds]
  );

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 2));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.3));
  const handleReset = () => {
    setZoom(TREE_CONFIG.zoom);
    setTranslate({ x: dimensions.width / 2, y: 50 });
  };
  const handleFit = () => {
    // Fit the tree to the container
    const nodeCount = nodes.length;
    const optimalZoom = Math.max(0.4, Math.min(1, 8 / nodeCount));
    setZoom(optimalZoom);
    setTranslate({ x: dimensions.width / 2, y: 50 });
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
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Vencedor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Ativo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-slate-400" />
          <span>Dominado</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Falhou</span>
        </div>
      </div>
    </div>
  );
}
