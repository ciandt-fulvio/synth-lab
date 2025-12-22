// src/components/interviews/LiveInterviewGrid.tsx
// Grid container for displaying multiple live interview cards
//
// Purpose: Render all active interviews from a research execution
// in a responsive two-column grid layout with real-time SSE updates
//
// Related:
// - Hook: src/hooks/use-live-interviews.ts
// - Card component: src/components/interviews/LiveInterviewCard.tsx
// - Type definitions: src/types/sse-events.ts

import { useState } from 'react';
import { useLiveInterviews } from '@/hooks/use-live-interviews';
import { LiveInterviewCard } from './LiveInterviewCard';
import { TranscriptDialog } from '@/components/shared/TranscriptDialog';
import { AlertCircle, Loader2, WifiOff } from 'lucide-react';
import type { LiveInterviewGridProps } from '@/types/sse-events';

/**
 * LiveInterviewGrid - Display all live interviews in a grid layout
 *
 * Features:
 * - Two-column grid layout (responsive: single column on mobile)
 * - Real-time message updates via SSE
 * - Click card to open full TranscriptDialog
 * - Connection status indicator
 * - Loading and error states
 *
 * @param props - Component props
 * @param props.execId - Research execution ID to stream interviews from
 * @param props.onExecutionCompleted - Optional callback when execution completes
 */
export function LiveInterviewGrid({ execId, onExecutionCompleted }: LiveInterviewGridProps) {
  const { messagesBySynth, synthIds, isConnected, error } =
    useLiveInterviews(execId, onExecutionCompleted);
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);

  // Handle card click to open transcript dialog
  const handleCardClick = (synthId: string) => {
    setSelectedSynthId(synthId);
  };

  // Handle dialog close
  const handleDialogClose = () => {
    setSelectedSynthId(null);
  };

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-destructive">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>Erro ao conectar: {error.message}</span>
      </div>
    );
  }

  // Loading state (no interviews yet, but connected)
  if (synthIds.length === 0 && isConnected) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
        <span>Aguardando entrevistas...</span>
      </div>
    );
  }

  // Disconnected state
  if (!isConnected && synthIds.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <WifiOff className="h-5 w-5 mr-2" />
        <span>Conectando ao stream...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Connection status indicator */}
      {!isConnected && synthIds.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200 rounded-md text-sm">
          <WifiOff className="h-4 w-4" />
          <span>Reconectando...</span>
        </div>
      )}

      {/* Grid of live interview cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {synthIds.map((synthId) => (
          <LiveInterviewCard
            key={synthId}
            execId={execId}
            synthId={synthId}
            messages={messagesBySynth[synthId]}
            onClick={handleCardClick}
          />
        ))}
      </div>

      {/* Transcript dialog for detailed view */}
      {selectedSynthId && (
        <TranscriptDialog
          execId={execId}
          synthId={selectedSynthId}
          open={!!selectedSynthId}
          onOpenChange={(open) => {
            if (!open) handleDialogClose();
          }}
        />
      )}
    </div>
  );
}
