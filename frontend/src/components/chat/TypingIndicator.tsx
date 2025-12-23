// src/components/chat/TypingIndicator.tsx
//
// Purpose: Animated typing indicator shown while synth is generating a response.
//
// Related:
// - SynthChatDialog: Shows this while waiting for synth response

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Bot } from 'lucide-react';

interface TypingIndicatorProps {
  synthName?: string;
  synthAvatarUrl?: string;
}

export function TypingIndicator({
  synthName = 'Synth',
  synthAvatarUrl,
}: TypingIndicatorProps) {
  const firstName = synthName?.split(' ')[0] || 'Synth';

  return (
    <div className="flex gap-3 flex-row">
      {/* Avatar */}
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarImage src={synthAvatarUrl} alt={firstName} />
        <AvatarFallback className="bg-green-100">
          <Bot className="h-4 w-4 text-green-600" />
        </AvatarFallback>
      </Avatar>

      {/* Typing bubble */}
      <div className="bg-white border border-gray-200 rounded-lg rounded-bl-none px-4 py-3">
        <div className="flex gap-1">
          <span
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  );
}
