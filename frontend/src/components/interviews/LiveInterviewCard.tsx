// src/components/interviews/LiveInterviewCard.tsx
// Live interview card component for real-time message display
//
// Purpose: Display a single interview's messages in a compact card format
// with 120px fixed height, smart auto-scrolling with "new messages" badge,
// and click to open full TranscriptDialog
//
// Related:
// - Type definitions: src/types/sse-events.ts
// - Message utilities: src/lib/message-utils.ts
// - Parent component: src/components/interviews/LiveInterviewGrid.tsx

import { useEffect, useRef, useState, memo, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { User, Loader2, CheckCircle2, ChevronDown } from 'lucide-react';
import { getSynth, getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import type { LiveInterviewCardProps, InterviewMessageEvent } from '@/types/sse-events';
import { extractMessageText } from '@/lib/message-utils';

/**
 * Get border color based on sentiment score (1-5)
 * 1 = Very negative (#ec9c9c - red)
 * 3 = Neutral (#e2e8f0 - gray)
 * 5 = Very positive (#a1ec9c - green)
 */
function getSentimentBorderColor(sentiment: number | null | undefined): string {
  if (sentiment === null || sentiment === undefined) {
    return '#e2e8f0'; // Default neutral
  }

  // Clamp sentiment to 1-5
  const s = Math.max(1, Math.min(5, sentiment));

  // Color stops
  const colors = {
    1: { r: 236, g: 156, b: 156 }, // #ec9c9c - very negative
    3: { r: 226, g: 232, b: 240 }, // #e2e8f0 - neutral
    5: { r: 161, g: 236, b: 156 }, // #a1ec9c - very positive
  };

  // Interpolate between color stops
  let r: number, g: number, b: number;

  if (s <= 3) {
    // Interpolate between 1 and 3
    const t = (s - 1) / 2;
    r = Math.round(colors[1].r + t * (colors[3].r - colors[1].r));
    g = Math.round(colors[1].g + t * (colors[3].g - colors[1].g));
    b = Math.round(colors[1].b + t * (colors[3].b - colors[1].b));
  } else {
    // Interpolate between 3 and 5
    const t = (s - 3) / 2;
    r = Math.round(colors[3].r + t * (colors[5].r - colors[3].r));
    g = Math.round(colors[3].g + t * (colors[5].g - colors[3].g));
    b = Math.round(colors[3].b + t * (colors[5].b - colors[3].b));
  }

  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Get the latest sentiment from messages (from Interviewer messages only)
 */
function getLatestSentiment(messages: InterviewMessageEvent[]): number | null {
  // Find the last message with a sentiment value (from Interviewer)
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.speaker === 'Interviewer' && msg.sentiment !== null && msg.sentiment !== undefined) {
      return msg.sentiment;
    }
  }
  return null;
}

/**
 * LiveInterviewCard - Compact real-time interview message display
 *
 * Features:
 * - 120px fixed height with internal scrolling (compact layout)
 * - Smart auto-scroll: pauses when user scrolls up, shows "new messages" badge
 * - Speaker color coding (blue for Interviewer, green for Interviewee)
 * - Click to open full transcript dialog (only when interview is completed)
 * - Visual indicator when interview is completed (checkmark icon)
 * - Smaller fonts (text-xs) for better density
 *
 * @param props - Component props
 * @param props.execId - Research execution ID
 * @param props.synthId - Synth participant ID
 * @param props.messages - Array of interview messages
 * @param props.isCompleted - Whether this interview has finished
 * @param props.onClick - Callback when card is clicked
 */
export const LiveInterviewCard = memo(function LiveInterviewCard({
  execId,
  synthId,
  messages,
  isCompleted,
  onClick,
}: LiveInterviewCardProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const lastSeenMessageCount = useRef(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch synth data for avatar and name display
  const { data: synth, isLoading: isLoadingSynth } = useQuery({
    queryKey: queryKeys.synthDetail(synthId),
    queryFn: () => getSynth(synthId),
  });

  // Extract first name and age from synth data
  const firstName = synth?.nome?.split(' ')[0] || 'Synth';
  const age = synth?.demografia?.idade;
  const cardTitle = age
    ? `${firstName}, ${age}`
    : firstName;

  // Smart scroll: only auto-scroll if user hasn't scrolled up
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    if (userHasScrolled) {
      // User scrolled up - count new messages instead of scrolling
      const newCount = messages.length - lastSeenMessageCount.current;
      if (newCount > 0) {
        setNewMessagesCount(newCount);
      }
    } else {
      // User at bottom - smooth scroll by incrementing scrollTop
      const scrollToBottom = () => {
        container.scrollTop = container.scrollHeight;
      };
      // Small delay to ensure DOM is updated
      requestAnimationFrame(scrollToBottom);
      lastSeenMessageCount.current = messages.length;
      setNewMessagesCount(0);
    }
  }, [messages, userHasScrolled]);

  // Detect user scrolling to pause/resume auto-scroll
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const target = event.currentTarget;
    const scrolledFromBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight;

    // If user scrolled more than 30px from bottom, pause auto-scroll
    if (scrolledFromBottom > 30) {
      setUserHasScrolled(true);
    } else {
      // User scrolled back to bottom
      setUserHasScrolled(false);
      setNewMessagesCount(0);
      lastSeenMessageCount.current = messages.length;
    }
  }, [messages.length]);

  // Handle clicking the "new messages" badge
  const handleNewMessagesBadgeClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Don't trigger card click
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
    setUserHasScrolled(false);
    setNewMessagesCount(0);
    lastSeenMessageCount.current = messages.length;
  }, [messages.length]);

  // Handle card click - allow anytime to see full transcript
  const handleCardClick = () => {
    onClick(synthId);
  };

  // Calculate border color based on latest sentiment
  const latestSentiment = useMemo(() => getLatestSentiment(messages), [messages]);
  const borderColor = useMemo(() => getSentimentBorderColor(latestSentiment), [latestSentiment]);

  return (
    <Card
      className="transition-all duration-300 cursor-pointer hover:shadow-lg"
      style={{ borderColor, borderWidth: '2px' }}
      onClick={handleCardClick}
    >
      <CardHeader className="py-2 px-3">
        <div className="flex items-center gap-2">
          <div className="relative flex-shrink-0">
            <Avatar className="h-7 w-7">
              <AvatarImage
                src={getSynthAvatarUrl(synthId)}
                alt={firstName}
              />
              <AvatarFallback>
                <User className="h-3.5 w-3.5" />
              </AvatarFallback>
            </Avatar>
            {isCompleted && (
              <div className="absolute -bottom-0.5 -right-0.5 bg-white rounded-full">
                <CheckCircle2 className="h-3 w-3 text-green-500" />
              </div>
            )}
          </div>
          <CardTitle className="text-xs font-medium truncate">
            {isLoadingSynth ? (
              <div className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>...</span>
              </div>
            ) : (
              cardTitle
            )}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0 relative">
        <div
          className="h-[100px] px-3 pb-2 overflow-y-auto scrollbar-thin"
          onScroll={handleScroll}
          ref={scrollContainerRef}
        >
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-xs text-muted-foreground">
              Aguardando...
            </div>
          ) : (
            <div className="space-y-0.5">
              {messages.map((msg, index) => {
                const isInterviewer = msg.speaker === 'Interviewer';

                return (
                  <div
                    key={`${msg.synth_id}-${msg.turn_number}-${msg.speaker}-${index}`}
                    className={`text-[11px] leading-tight px-1.5 py-0.5 rounded ${
                      isInterviewer
                        ? 'bg-blue-50 border-l-2 border-blue-400'
                        : 'bg-green-50 border-l-2 border-green-400'
                    }`}
                  >
                    <span className="text-foreground">
                      {extractMessageText(msg.text)}
                    </span>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        {/* New messages badge */}
        {newMessagesCount > 0 && (
          <button
            onClick={handleNewMessagesBadgeClick}
            className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-1 px-2 py-0.5 bg-indigo-600 text-white text-[10px] font-medium rounded-full shadow-lg hover:bg-indigo-700 transition-colors animate-pulse"
          >
            <ChevronDown className="h-3 w-3" />
            {newMessagesCount} nova{newMessagesCount > 1 ? 's' : ''}
          </button>
        )}
      </CardContent>
    </Card>
  );
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if messages, synthId, isCompleted, or sentiment changed
  const prevSentiment = getLatestSentiment(prevProps.messages);
  const nextSentiment = getLatestSentiment(nextProps.messages);
  return (
    prevProps.synthId === nextProps.synthId &&
    prevProps.isCompleted === nextProps.isCompleted &&
    prevProps.messages.length === nextProps.messages.length &&
    prevProps.messages[prevProps.messages.length - 1]?.turn_number ===
      nextProps.messages[nextProps.messages.length - 1]?.turn_number &&
    prevSentiment === nextSentiment
  );
});
