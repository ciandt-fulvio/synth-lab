// src/components/shared/TranscriptDialog.tsx

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Loader2, MessageCircle, User } from 'lucide-react';
import { getTranscript } from '@/services/research-api';
import { getSynth, getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import { extractMessageText } from '@/lib/message-utils';
import { SynthChatDialog } from '@/components/chat/SynthChatDialog';
import type { InterviewMessageEvent } from '@/types/sse-events';

interface TranscriptDialogProps {
  execId: string;
  synthId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Optional live messages from SSE streaming (used during live interviews) */
  liveMessages?: InterviewMessageEvent[];
  /** Whether the interview is still in progress */
  isLive?: boolean;
}

export function TranscriptDialog({
  execId,
  synthId,
  open,
  onOpenChange,
  liveMessages,
  isLive = false,
}: TranscriptDialogProps) {
  // State for chat dialog
  const [chatOpen, setChatOpen] = useState(false);

  // Fetch transcript from DB (only if not using live messages)
  const { data: transcript, isLoading: transcriptLoading } = useQuery({
    queryKey: queryKeys.researchTranscript(execId, synthId!),
    queryFn: () => getTranscript(execId, synthId!),
    enabled: open && !!synthId && !liveMessages,
  });

  // Fetch synth details for name and age
  const { data: synth, isLoading: synthLoading } = useQuery({
    queryKey: queryKeys.synthDetail(synthId!),
    queryFn: () => getSynth(synthId!),
    enabled: open && !!synthId,
  });

  // Use live messages if available, otherwise use transcript from DB
  const messages = liveMessages
    ? liveMessages.map(m => ({ speaker: m.speaker, text: m.text }))
    : transcript?.messages || [];

  const isLoading = !liveMessages && (transcriptLoading || synthLoading);

  // Get first name from synth nome
  const firstName = synth?.nome?.split(' ')[0] || 'Entrevistado';
  const age = synth?.demografia?.idade;

  // Build title
  const baseTitle = age
    ? `Entrevista com ${firstName}, ${age} anos`
    : `Entrevista com ${firstName}`;
  const title = isLive ? `${baseTitle} (ao vivo)` : baseTitle;

  // Check if interview is completed (has messages and status is 'completed')
  const isInterviewCompleted =
    !isLive &&
    transcript?.messages &&
    transcript.messages.length > 0 &&
    transcript.status === 'completed';

  // Map speaker to display name
  const getSpeakerName = (speaker: string): string => {
    if (speaker.toLowerCase() === 'interviewer') return 'SynthLab';
    return firstName;
  };

  // Get speaker style - using colors compatible with the design
  const getSpeakerStyle = (speaker: string): string => {
    if (speaker.toLowerCase() === 'interviewer') {
      return 'font-semibold'; // SynthLab in blue
    }
    return 'font-semibold'; // Interviewee in green
  };

  // Get speaker color
  const getSpeakerColor = (speaker: string): string => {
    if (speaker.toLowerCase() === 'interviewer') {
      return '#2563eb'; // Blue-600
    }
    return '#16a34a'; // Green-600
  };

  // Handle opening chat dialog - closes transcript and opens chat
  const handleOpenChat = () => {
    setChatOpen(true);
  };

  // Handle closing chat dialog - closes everything
  const handleCloseChat = (open: boolean) => {
    if (!open) {
      // When chat is closed, close everything
      setChatOpen(false);
      onOpenChange(false);
    }
  };

  // Handle closing transcript dialog
  const handleTranscriptClose = (open: boolean) => {
    if (!open) {
      setChatOpen(false);
    }
    onOpenChange(open);
  };

  return (
    <>
      <Dialog open={open && !chatOpen} onOpenChange={handleTranscriptClose}>
        <DialogContent className="sm:max-w-[70vw] h-[80vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <div className="flex items-center gap-3">
              {synthId && (
                <Avatar className="h-10 w-10">
                  <AvatarImage
                    src={getSynthAvatarUrl(synthId)}
                    alt={firstName}
                  />
                  <AvatarFallback>
                    <User className="h-5 w-5" />
                  </AvatarFallback>
                </Avatar>
              )}
              <DialogTitle>{title}</DialogTitle>
            </div>
          </DialogHeader>

          <div className="flex-grow overflow-y-auto px-6 py-4 bg-gray-50 rounded-md">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : messages.length > 0 ? (
              <div className="space-y-2">
                {messages.map((message, index) => {
                  const isInterviewer = message.speaker.toLowerCase() === 'interviewer';
                  return (
                    <div
                      key={index}
                      className={`pl-3 py-2 ${
                        isInterviewer
                          ? 'border-l-4 border-blue-400'
                          : 'border-l-4 border-green-400'
                      }`}
                    >
                      <span
                        className="font-semibold text-sm"
                        style={{ color: getSpeakerColor(message.speaker) }}
                      >
                        {getSpeakerName(message.speaker)}:
                      </span>
                      <p className="text-gray-700 mt-1 leading-relaxed">
                        {extractMessageText(message.text)}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                Nenhuma mensagem encontrada
              </div>
            )}
          </div>

          {/* "Conversar com {nome}" button - only shown when interview is completed */}
          {isInterviewCompleted && (
            <div className="flex-shrink-0 pt-4 border-t">
              <Button
                onClick={handleOpenChat}
                className="w-full"
                variant="default"
              >
                <MessageCircle className="h-4 w-4 mr-2" />
                Conversar com {firstName}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Chat dialog - opens when "Conversar" button is clicked */}
      {synthId && synth && (
        <SynthChatDialog
          synthId={synthId}
          synthName={synth.nome}
          synthAge={synth.demografia?.idade}
          execId={execId}
          open={chatOpen}
          onOpenChange={handleCloseChat}
        />
      )}
    </>
  );
}
