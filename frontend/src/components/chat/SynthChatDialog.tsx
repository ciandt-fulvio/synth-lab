// src/components/chat/SynthChatDialog.tsx
//
// Purpose: Dialog for chatting with a synth after an interview.
// Shows chat history and allows sending new messages.
//
// Related:
// - TranscriptDialog: Opens this dialog when "Conversar" button is clicked
// - chat-api.ts: API client for chat endpoint
// - use-synth-chat.ts: Hook for managing chat state

import { useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { User, AlertCircle } from 'lucide-react';
import { getSynthAvatarUrl } from '@/services/synths-api';
import { useSynthChat } from '@/hooks/use-synth-chat';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';

interface SynthChatDialogProps {
  synthId: string;
  synthName: string;
  synthAge?: number;
  execId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SynthChatDialog({
  synthId,
  synthName,
  synthAge,
  execId,
  open,
  onOpenChange,
}: SynthChatDialogProps) {
  // Chat state management
  const { messages, isLoading, error, sendMessage, clearError } = useSynthChat({
    synthId,
    synthName,
    synthAge,
    execId,
  });

  // Ref for auto-scrolling to bottom
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Build title: "Conversando com {nome}, {idade} anos"
  const firstName = synthName?.split(' ')[0] || 'Synth';
  const title = synthAge
    ? `Conversando com ${firstName}, ${synthAge} anos`
    : `Conversando com ${firstName}`;

  const avatarUrl = getSynthAvatarUrl(synthId);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[70vw] h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={avatarUrl} alt={firstName} />
              <AvatarFallback>
                <User className="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <DialogTitle>{title}</DialogTitle>
          </div>
        </DialogHeader>

        {/* Error alert */}
        {error && (
          <Alert variant="destructive" className="flex-shrink-0">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>{error}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearError}
                className="h-6 px-2"
              >
                Fechar
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Chat messages area */}
        <div className="flex-grow overflow-y-auto px-4 py-4 bg-gray-50 rounded-md space-y-4">
          {messages.length === 0 && !isLoading ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <p className="text-lg font-medium mb-2">
                  Inicie uma conversa com {firstName}
                </p>
                <p className="text-sm">
                  Faça perguntas sobre a entrevista ou explore novos tópicos.
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                  synthName={synthName}
                  synthAvatarUrl={avatarUrl}
                />
              ))}
              {isLoading && (
                <TypingIndicator
                  synthName={synthName}
                  synthAvatarUrl={avatarUrl}
                />
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Chat input area */}
        <div className="flex-shrink-0 pt-4">
          <ChatInput
            onSend={sendMessage}
            isLoading={isLoading}
            placeholder={`Mensagem para ${firstName}...`}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
