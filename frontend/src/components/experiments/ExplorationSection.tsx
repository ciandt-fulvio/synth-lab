/**
 * ExplorationSection component.
 *
 * Section in experiment detail page for managing explorations.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US1, US6)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useExplorations } from '@/hooks/use-exploration';
import { ExplorationList } from '@/components/exploration/ExplorationList';
import { NewExplorationDialog } from '@/components/exploration/NewExplorationDialog';
import { TreeDeciduous, Plus, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface ExplorationSectionProps {
  experimentId: string;
  hasAnalysis: boolean;
  baselineSuccessRate?: number | null;
}

export function ExplorationSection({
  experimentId,
  hasAnalysis,
  baselineSuccessRate,
}: ExplorationSectionProps) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isNewDialogOpen, setIsNewDialogOpen] = useState(false);

  const { data: explorations, isLoading } = useExplorations(experimentId);

  // Check if there's a running exploration
  const hasRunningExploration = explorations?.some((e) => e.status === 'running');

  // Button should be disabled if no analysis OR if an exploration is already running
  const isButtonDisabled = !hasAnalysis || hasRunningExploration;

  const handleExplorationSuccess = (explorationId: string) => {
    navigate(`/experiments/${experimentId}/explorations/${explorationId}`);
  };

  return (
    <div className="card">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 rounded-t-lg transition-colors">
            <div className="flex items-center gap-3">
              <div className="icon-box-light">
                <TreeDeciduous className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-card-title">Explorações de Cenários</h3>
                <p className="text-meta">
                  {explorations?.length || 0} exploração(ões)
                  {hasRunningExploration && ' • 1 em execução'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isOpen ? (
                <ChevronUp className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 pt-2 border-t">
            {/* Action Button */}
            <div className="flex justify-end mb-4">
              {isButtonDisabled && !hasRunningExploration ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span>
                      <Button disabled className="opacity-50">
                        <Plus className="mr-2 h-4 w-4" />
                        Iniciar Exploração
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="flex items-center gap-1.5">
                      <Info className="h-3.5 w-3.5" />
                      Execute uma análise primeiro
                    </p>
                  </TooltipContent>
                </Tooltip>
              ) : hasRunningExploration ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span>
                      <Button disabled className="opacity-50">
                        <Plus className="mr-2 h-4 w-4" />
                        Iniciar Exploração
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="flex items-center gap-1.5">
                      <Info className="h-3.5 w-3.5" />
                      Aguarde a exploração atual terminar
                    </p>
                  </TooltipContent>
                </Tooltip>
              ) : (
                <Button
                  onClick={() => setIsNewDialogOpen(true)}
                  className="btn-primary"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Iniciar Exploração
                </Button>
              )}
            </div>

            {/* Explorations List */}
            <ExplorationList
              explorations={explorations}
              experimentId={experimentId}
              isLoading={isLoading}
            />
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* New Exploration Dialog */}
      <NewExplorationDialog
        open={isNewDialogOpen}
        onOpenChange={setIsNewDialogOpen}
        experimentId={experimentId}
        baselineSuccessRate={baselineSuccessRate}
        onSuccess={handleExplorationSuccess}
      />
    </div>
  );
}
