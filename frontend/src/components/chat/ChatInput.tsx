// src/components/chat/ChatInput.tsx
//
// Purpose: Input component for chat messages with send button and Enter key support.
//
// Related:
// - SynthChatDialog: Parent component that uses this input

import { useState, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  isLoading = false,
  placeholder = 'Digite sua mensagem...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled && !isLoading) {
      onSend(trimmedMessage);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled = disabled || isLoading || !message.trim();

  return (
    <div className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isLoading}
        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <Button
        onClick={handleSend}
        disabled={isDisabled}
        className="min-w-[80px]"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <>
            <Send className="h-4 w-4 mr-2" />
            Enviar
          </>
        )}
      </Button>
    </div>
  );
}
