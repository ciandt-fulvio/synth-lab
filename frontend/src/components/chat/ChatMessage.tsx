// src/components/chat/ChatMessage.tsx
//
// Purpose: Single chat message bubble with styling based on role (user or synth).
//
// Related:
// - SynthChatDialog: Parent component that renders messages
// - ChatMessage type from types/chat.ts

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { User, Bot } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatMessageProps {
  message: ChatMessageType;
  synthName?: string;
  synthAvatarUrl?: string;
}

export function ChatMessage({
  message,
  synthName = 'Synth',
  synthAvatarUrl,
}: ChatMessageProps) {
  const isUser = message.role === 'user';
  const firstName = synthName?.split(' ')[0] || 'Synth';

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 flex-shrink-0">
        {isUser ? (
          <AvatarFallback className="bg-blue-100">
            <User className="h-4 w-4 text-blue-600" />
          </AvatarFallback>
        ) : (
          <>
            <AvatarImage src={synthAvatarUrl} alt={firstName} />
            <AvatarFallback className="bg-green-100">
              <Bot className="h-4 w-4 text-green-600" />
            </AvatarFallback>
          </>
        )}
      </Avatar>

      {/* Message bubble */}
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
        }`}
      >
        {/* Speaker name */}
        <div
          className={`text-xs mb-1 font-medium ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}
        >
          {isUser ? 'Você' : firstName}
        </div>

        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

        {/* Timestamp */}
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-200' : 'text-gray-400'
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
