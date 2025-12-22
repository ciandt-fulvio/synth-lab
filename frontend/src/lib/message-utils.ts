// src/lib/message-utils.ts
// Utility functions for processing interview message text
//
// Extracted from TranscriptDialog for reuse in LiveInterviewCard

/**
 * Extract message text from potentially JSON-formatted response.
 * If the text is a JSON object with a "message" field, extract it.
 * Otherwise, return the original text.
 *
 * Handles malformed JSON where newlines inside strings are not properly escaped.
 *
 * @param text - Raw message text (may be JSON string or plain text)
 * @returns Extracted human-readable message text
 *
 * @example
 * // JSON-formatted message
 * extractMessageText('{"message": "Eu prefiro Amazon.", "should_end": false}')
 * // → "Eu prefiro Amazon."
 *
 * @example
 * // Malformed JSON (newlines)
 * extractMessageText('{"message": "Linha 1\nLinha 2", "should_end": false}')
 * // → "Linha 1\nLinha 2"
 *
 * @example
 * // Plain text
 * extractMessageText('Hello, how are you?')
 * // → "Hello, how are you?"
 */
export function extractMessageText(text: string): string {
  // Check if text looks like JSON (starts with { and ends with })
  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    // First try parsing as-is
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed && typeof parsed.message === 'string') {
        return parsed.message;
      }
      // If parsed successfully but no message field, return original
      console.warn('[extractMessageText] JSON parsed but no message field:', parsed);
    } catch (parseError) {
      // JSON parse failed - likely has unescaped newlines inside strings
      console.log('[extractMessageText] JSON parse failed, trying regex extraction');

      // Use regex to extract the message field directly
      // Match: "message": "..." where the value can contain anything until we hit
      // the pattern for the next field or end of object
      const messageMatch = trimmed.match(/"message"\s*:\s*"([\s\S]*?)"\s*,\s*"/);
      if (messageMatch && messageMatch[1]) {
        // Unescape any escaped characters
        return messageMatch[1]
          .replace(/\\n/g, '\n')
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\');
      }

      // Alternative: try to find message field ending with ", "should_end" or similar
      const altMatch = trimmed.match(
        /"message"\s*:\s*"([\s\S]*?)"\s*,[\s\n]*"(?:should_end|internal_notes)/
      );
      if (altMatch && altMatch[1]) {
        return altMatch[1]
          .replace(/\\n/g, '\n')
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\');
      }

      console.warn('[extractMessageText] Could not extract message from JSON-like text:', trimmed.substring(0, 100) + '...');
    }
  }
  return text;
}
