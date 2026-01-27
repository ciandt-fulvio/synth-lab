/**
 * DAGEdgeControls component for managing DAG edges.
 *
 * Provides UI for adding, editing, and removing edges.
 *
 * References:
 *   - Types: types/causal-dag.ts
 *   - Hook: hooks/use-dag.ts
 */

import { useState } from 'react';
import { Plus, Trash2, ArrowRight, Link2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import type { Variable, Edge, RelationshipType } from '@/types/causal-dag';

interface DAGEdgeControlsProps {
  /**
   * Available nodes for edge creation.
   */
  nodes: Variable[];

  /**
   * Current edges.
   */
  edges: Edge[];

  /**
   * Callback when an edge is added.
   */
  onAddEdge?: (edge: Edge) => void;

  /**
   * Callback when an edge is removed.
   */
  onRemoveEdge?: (source: string, target: string) => void;

  /**
   * Whether controls are disabled.
   */
  disabled?: boolean;
}

/**
 * DAGEdgeControls component.
 *
 * @example
 * <DAGEdgeControls
 *   nodes={dag.nodes}
 *   edges={dag.edges}
 *   onAddEdge={handleAddEdge}
 *   onRemoveEdge={handleRemoveEdge}
 * />
 */
export function DAGEdgeControls({
  nodes,
  edges,
  onAddEdge,
  onRemoveEdge,
  disabled = false,
}: DAGEdgeControlsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [relationshipType, setRelationshipType] =
    useState<RelationshipType>('causal');
  const [strength, setStrength] = useState('');
  const [description, setDescription] = useState('');

  // Get valid targets (exclude source and already connected nodes)
  const getValidTargets = () => {
    if (!source) return nodes;
    const existingTargets = edges
      .filter((e) => e.source === source)
      .map((e) => e.target);
    return nodes.filter(
      (n) => n.name !== source && !existingTargets.includes(n.name)
    );
  };

  const handleSubmit = () => {
    if (!source || !target) return;

    const newEdge: Edge = {
      source,
      target,
      relationship_type: relationshipType,
      strength: strength ? parseFloat(strength) : null,
      description: description || null,
    };

    onAddEdge?.(newEdge);
    resetForm();
    setIsOpen(false);
  };

  const resetForm = () => {
    setSource('');
    setTarget('');
    setRelationshipType('causal');
    setStrength('');
    setDescription('');
  };

  return (
    <div className="space-y-4">
      {/* Add Edge Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || nodes.length < 2}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Edge
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Edge</DialogTitle>
            <DialogDescription>
              Create a causal relationship between two variables.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Source */}
            <div className="space-y-2">
              <Label>Source Variable</Label>
              <Select value={source} onValueChange={setSource}>
                <SelectTrigger>
                  <SelectValue placeholder="Select source..." />
                </SelectTrigger>
                <SelectContent>
                  {nodes
                    .filter((n) => n.variable_type !== 'output')
                    .map((node) => (
                      <SelectItem key={node.name} value={node.name}>
                        {node.label} ({node.name})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {/* Target */}
            <div className="space-y-2">
              <Label>Target Variable</Label>
              <Select
                value={target}
                onValueChange={setTarget}
                disabled={!source}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select target..." />
                </SelectTrigger>
                <SelectContent>
                  {getValidTargets()
                    .filter((n) => n.variable_type !== 'input')
                    .map((node) => (
                      <SelectItem key={node.name} value={node.name}>
                        {node.label} ({node.name})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {/* Relationship Type */}
            <div className="space-y-2">
              <Label>Relationship Type</Label>
              <Select
                value={relationshipType}
                onValueChange={(v) => setRelationshipType(v as RelationshipType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="causal">Causal</SelectItem>
                  <SelectItem value="correlation">Correlation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Strength */}
            <div className="space-y-2">
              <Label>Strength (optional, -1 to 1)</Label>
              <Input
                type="number"
                min="-1"
                max="1"
                step="0.1"
                value={strength}
                onChange={(e) => setStrength(e.target.value)}
                placeholder="e.g., 0.8"
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label>Description (optional)</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the relationship..."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!source || !target}>
              Add Edge
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edge List */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-slate-700">
          Edges ({edges.length})
        </h4>
        {edges.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No edges yet</p>
        ) : (
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {edges.map((edge) => {
              const sourceNode = nodes.find((n) => n.name === edge.source);
              const targetNode = nodes.find((n) => n.name === edge.target);

              return (
                <div
                  key={`${edge.source}-${edge.target}`}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <Link2 className="h-4 w-4 text-slate-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-slate-700 truncate">
                      {sourceNode?.label || edge.source}
                    </span>
                    <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-slate-700 truncate">
                      {targetNode?.label || edge.target}
                    </span>
                    {edge.strength !== null && (
                      <span className="text-xs text-slate-500 flex-shrink-0">
                        ({edge.strength > 0 ? '+' : ''}
                        {edge.strength.toFixed(1)})
                      </span>
                    )}
                  </div>
                  {onRemoveEdge && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-red-600 hover:text-red-700 flex-shrink-0"
                      onClick={() => onRemoveEdge(edge.source, edge.target)}
                      disabled={disabled}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
