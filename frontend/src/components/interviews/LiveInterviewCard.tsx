// src/components/interviews/LiveInterviewCard.tsx
// Live interview card component for real-time message display
//
// Purpose: Display a single interview's messages in a compact card format
// with 200px fixed height, auto-scrolling to newest messages, and click
// to open full TranscriptDialog
//
// Related:
// - Type definitions: src/types/sse-events.ts
// - Message utilities: src/lib/message-utils.ts
// - Parent component: src/components/interviews/LiveInterviewGrid.tsx

import { useEffect, useRef, useState, memo, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { User, Loader2, CheckCircle2 } from 'lucide-react';
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
 * - 200px fixed height with internal scrolling
 * - Auto-scroll to newest messages (with user scroll detection)
 * - Speaker color coding (blue for Interviewer, green for Interviewee)
 * - Click to open full transcript dialog (only when interview is completed)
 * - Visual indicator when interview is completed (checkmark icon)
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
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const lastMessageRef = useRef<HTMLDivElement>(null);

  // Fetch synth data for avatar and name display
  const { data: synth, isLoading: isLoadingSynth } = useQuery({
    queryKey: queryKeys.synthDetail(synthId),
    queryFn: () => getSynth(synthId),
  });

  // Extract first name and age from synth data
  const firstName = synth?.nome?.split(' ')[0] || 'Synth';
  const age = synth?.demografia?.idade;
  const cardTitle = age
    ? `Entrevista com ${firstName}, ${age} anos`
    : `Entrevista com ${firstName}`;

  // Auto-scroll to newest message when new messages arrive
  useEffect(() => {
    if (!userHasScrolled && lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, userHasScrolled]);

  // Detect user scrolling up to pause auto-scroll
  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const target = event.currentTarget;
    const scrolledFromBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight;

    // If user scrolled more than 50px from bottom, pause auto-scroll
    if (scrolledFromBottom > 50) {
      setUserHasScrolled(true);
    } else {
      setUserHasScrolled(false);
    }
  };

  // Handle card click - only allow when interview is completed
  const handleCardClick = () => {
    if (isCompleted) {
      onClick(synthId);
    }
  };

  // Calculate border color based on latest sentiment
  const latestSentiment = useMemo(() => getLatestSentiment(messages), [messages]);
  const borderColor = useMemo(() => getSentimentBorderColor(latestSentiment), [latestSentiment]);

  return (
    <Card
      className={`transition-all duration-300 ${
        isCompleted
          ? 'cursor-pointer hover:shadow-lg'
          : 'cursor-default opacity-90'
      }`}
      style={{ borderColor, borderWidth: '2px' }}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Avatar className="h-10 w-10">
              <AvatarImage
                src={getSynthAvatarUrl(synthId)}
                alt={firstName}
              />
              <AvatarFallback>
                <User className="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            {isCompleted && (
              <div className="absolute -bottom-1 -right-1 bg-white rounded-full">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              </div>
            )}
          </div>
          <CardTitle className="text-sm">
            {isLoadingSynth ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Carregando...</span>
              </div>
            ) : (
              cardTitle
            )}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea
          className="h-[150px] px-4 pb-4"
          onScrollCapture={handleScroll}
          ref={scrollAreaRef}
        >
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              Aguardando mensagens...
            </div>
          ) : (
            <div className="space-y-2">
              {messages.map((msg, index) => {
                const isLast = index === messages.length - 1;
                const speakerColor =
                  msg.speaker === 'Interviewer'
                    ? 'text-[#2563eb]' // Blue for Interviewer
                    : 'text-[#16a34a]'; // Green for Interviewee

                return (
                  <div
                    key={`${msg.synth_id}-${msg.turn_number}`}
                    ref={isLast ? lastMessageRef : null}
                    className="text-sm"
                  >
                    <span className={`font-medium ${speakerColor}`}>
                      {msg.speaker === 'Interviewer' ? 'SynthLab' : msg.speaker}:
                    </span>{' '}
                    <span className="text-foreground">
                      {extractMessageText(msg.text)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
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
