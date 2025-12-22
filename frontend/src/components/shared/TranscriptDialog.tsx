// src/components/shared/TranscriptDialog.tsx

import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Loader2, User } from 'lucide-react';
import { getTranscript } from '@/services/research-api';
import { getSynth, getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import { extractMessageText } from '@/lib/message-utils';

interface TranscriptDialogProps {
  execId: string;
  synthId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TranscriptDialog({
  execId,
  synthId,
  open,
  onOpenChange,
}: TranscriptDialogProps) {
  // Fetch transcript
  const { data: transcript, isLoading: transcriptLoading } = useQuery({
    queryKey: queryKeys.researchTranscript(execId, synthId!),
    queryFn: () => getTranscript(execId, synthId!),
    enabled: open && !!synthId,
  });

  // Fetch synth details for name and age
  const { data: synth, isLoading: synthLoading } = useQuery({
    queryKey: queryKeys.synthDetail(synthId!),
    queryFn: () => getSynth(synthId!),
    enabled: open && !!synthId,
  });

  const isLoading = transcriptLoading || synthLoading;

  // Get first name from synth nome
  const firstName = synth?.nome?.split(' ')[0] || 'Entrevistado';
  const age = synth?.demografia?.idade;

  // Build title
  const title = age
    ? `Entrevista com ${firstName}, ${age} anos`
    : `Entrevista com ${firstName}`;

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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
          ) : transcript?.messages && transcript.messages.length > 0 ? (
            <div className="transcript-content space-y-5">
              {transcript.messages.map((message, index) => (
                <p key={index} className="leading-relaxed">
                  <span
                    className={getSpeakerStyle(message.speaker)}
                    style={{ color: getSpeakerColor(message.speaker) }}
                  >
                    {getSpeakerName(message.speaker)}:
                  </span>{' '}
                  <span className="text-gray-700">
                    {extractMessageText(message.text)}
                  </span>
                </p>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Nenhuma mensagem encontrada
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
