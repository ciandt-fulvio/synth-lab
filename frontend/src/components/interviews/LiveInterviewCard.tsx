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

import { useEffect, useRef, useState, memo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { User, Loader2 } from 'lucide-react';
import { getSynth, getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import type { LiveInterviewCardProps } from '@/types/sse-events';
import { extractMessageText } from '@/lib/message-utils';

/**
 * LiveInterviewCard - Compact real-time interview message display
 *
 * Features:
 * - 200px fixed height with internal scrolling
 * - Auto-scroll to newest messages (with user scroll detection)
 * - Speaker color coding (blue for Interviewer, green for Interviewee)
 * - Click to open full transcript dialog
 *
 * @param props - Component props
 * @param props.execId - Research execution ID
 * @param props.synthId - Synth participant ID
 * @param props.messages - Array of interview messages
 * @param props.onClick - Callback when card is clicked
 */
export const LiveInterviewCard = memo(function LiveInterviewCard({
  execId,
  synthId,
  messages,
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

  // Handle card click
  const handleCardClick = () => {
    onClick(synthId);
  };

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={handleCardClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarImage
              src={getSynthAvatarUrl(synthId)}
              alt={firstName}
            />
            <AvatarFallback>
              <User className="h-5 w-5" />
            </AvatarFallback>
          </Avatar>
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
          className="h-[200px] px-4 pb-4"
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
  // Custom comparison: only re-render if messages or synthId changed
  return (
    prevProps.synthId === nextProps.synthId &&
    prevProps.messages.length === nextProps.messages.length &&
    prevProps.messages[prevProps.messages.length - 1]?.turn_number ===
      nextProps.messages[nextProps.messages.length - 1]?.turn_number
  );
});
