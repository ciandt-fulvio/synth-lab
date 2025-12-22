// tests/hooks/use-live-interviews.test.ts
// Unit tests for useLiveInterviews hook - Message aggregation by synth_id
//
// TDD: These tests are written FIRST and should FAIL until useLiveInterviews is implemented

import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLiveInterviews } from '@/hooks/use-live-interviews';
import type { InterviewMessageEvent } from '@/types/sse-events';

// Mock useSSE hook
vi.mock('@/hooks/use-sse', () => ({
  useSSE: vi.fn((execId, enabled, onMessage) => {
    // Store onMessage for testing
    (global as any).mockOnMessage = onMessage;
    return {
      isConnected: true,
      error: null,
    };
  }),
}));

describe('useLiveInterviews hook', () => {
  it('should initialize with empty messages', () => {
    const { result } = renderHook(() => useLiveInterviews('exec-123'));

    expect(result.current.messagesBySynth).toEqual({});
    expect(result.current.synthIds).toEqual([]);
    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should aggregate messages by synth_id', async () => {
    const { result } = renderHook(() => useLiveInterviews('exec-123'));

    const message1: InterviewMessageEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-456',
      turn_number: 1,
      speaker: 'Interviewer',
      text: 'Hello',
      timestamp: '2025-12-21T10:00:00Z',
      is_replay: false,
    };

    const message2: InterviewMessageEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-456',
      turn_number: 2,
      speaker: 'Interviewee',
      text: 'Hi there',
      timestamp: '2025-12-21T10:00:05Z',
      is_replay: false,
    };

    // Simulate messages via useSSE callback
    act(() => {
      if ((global as any).mockOnMessage) {
        (global as any).mockOnMessage(message1);
      }
    });

    await waitFor(() => {
      expect(result.current.messagesBySynth['synth-456']).toHaveLength(1);
    });

    act(() => {
      if ((global as any).mockOnMessage) {
        (global as any).mockOnMessage(message2);
      }
    });

    await waitFor(() => {
      expect(result.current.messagesBySynth['synth-456']).toHaveLength(2);
      expect(result.current.messagesBySynth['synth-456'][0]).toEqual(message1);
      expect(result.current.messagesBySynth['synth-456'][1]).toEqual(message2);
    });
  });

  it('should maintain separate message arrays for different synths', async () => {
    const { result } = renderHook(() => useLiveInterviews('exec-123'));

    const message1: InterviewMessageEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-111',
      turn_number: 1,
      speaker: 'Interviewer',
      text: 'Hello synth 1',
      timestamp: '2025-12-21T10:00:00Z',
      is_replay: false,
    };

    const message2: InterviewMessageEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-222',
      turn_number: 1,
      speaker: 'Interviewer',
      text: 'Hello synth 2',
      timestamp: '2025-12-21T10:00:00Z',
      is_replay: false,
    };

    act(() => {
      if ((global as any).mockOnMessage) {
        (global as any).mockOnMessage(message1);
        (global as any).mockOnMessage(message2);
      }
    });

    await waitFor(() => {
      expect(result.current.synthIds).toHaveLength(2);
      expect(result.current.synthIds).toContain('synth-111');
      expect(result.current.synthIds).toContain('synth-222');
      expect(result.current.messagesBySynth['synth-111']).toHaveLength(1);
      expect(result.current.messagesBySynth['synth-222']).toHaveLength(1);
    });
  });

  it('should provide synthIds array from messagesBySynth keys', async () => {
    const { result } = renderHook(() => useLiveInterviews('exec-123'));

    expect(result.current.synthIds).toEqual([]);

    const message: InterviewMessageEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-789',
      turn_number: 1,
      speaker: 'Interviewer',
      text: 'Test',
      timestamp: '2025-12-21T10:00:00Z',
      is_replay: false,
    };

    act(() => {
      if ((global as any).mockOnMessage) {
        (global as any).mockOnMessage(message);
      }
    });

    await waitFor(() => {
      expect(result.current.synthIds).toContain('synth-789');
    });
  });

  it('should preserve message order within synth arrays', async () => {
    const { result } = renderHook(() => useLiveInterviews('exec-123'));

    const messages: InterviewMessageEvent[] = [
      {
        event_type: 'message',
        exec_id: 'exec-123',
        synth_id: 'synth-456',
        turn_number: 1,
        speaker: 'Interviewer',
        text: 'First',
        timestamp: '2025-12-21T10:00:00Z',
        is_replay: false,
      },
      {
        event_type: 'message',
        exec_id: 'exec-123',
        synth_id: 'synth-456',
        turn_number: 2,
        speaker: 'Interviewee',
        text: 'Second',
        timestamp: '2025-12-21T10:00:05Z',
        is_replay: false,
      },
      {
        event_type: 'message',
        exec_id: 'exec-123',
        synth_id: 'synth-456',
        turn_number: 3,
        speaker: 'Interviewer',
        text: 'Third',
        timestamp: '2025-12-21T10:00:10Z',
        is_replay: false,
      },
    ];

    act(() => {
      messages.forEach((msg) => {
        if ((global as any).mockOnMessage) {
          (global as any).mockOnMessage(msg);
        }
      });
    });

    await waitFor(() => {
      const synthMessages = result.current.messagesBySynth['synth-456'];
      expect(synthMessages).toHaveLength(3);
      expect(synthMessages[0].text).toBe('First');
      expect(synthMessages[1].text).toBe('Second');
      expect(synthMessages[2].text).toBe('Third');
    });
  });
});
