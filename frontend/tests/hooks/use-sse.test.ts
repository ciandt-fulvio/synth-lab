// tests/hooks/use-sse.test.ts
// Unit tests for useSSE hook - EventSource connection management
//
// TDD: These tests are written FIRST and should FAIL until useSSE is implemented

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useSSE } from '@/hooks/use-sse';

// Mock EventSource
class MockEventSource {
  url: string;
  readyState: number = 0; // CONNECTING
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  listeners: Map<string, ((event: MessageEvent) => void)[]> = new Map();

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(listener);
  }

  close() {
    this.readyState = 2; // CLOSED
  }

  // Test helper to simulate events
  simulateMessage(data: string, eventType = 'message') {
    const listeners = this.listeners.get(eventType) || [];
    const event = new MessageEvent(eventType, { data });
    listeners.forEach((listener) => listener(event));
  }
}

// Replace global EventSource
global.EventSource = MockEventSource as any;

describe('useSSE hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with disconnected state when disabled', () => {
    const { result } = renderHook(() =>
      useSSE('exec-123', false, vi.fn())
    );

    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should establish EventSource connection when enabled', async () => {
    const { result } = renderHook(() =>
      useSSE('exec-123', true, vi.fn())
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
    expect(result.current.error).toBeNull();
  });

  it('should call onMessage callback when message event received', async () => {
    const onMessage = vi.fn();
    const { result } = renderHook(() =>
      useSSE('exec-123', true, onMessage)
    );

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Simulate message event
    const mockEvent = {
      event_type: 'message',
      exec_id: 'exec-123',
      synth_id: 'synth-456',
      turn_number: 1,
      speaker: 'Interviewer',
      text: 'Hello',
      timestamp: '2025-12-21T10:00:00Z',
      is_replay: false,
    };

    // Get the EventSource instance and simulate message
    const eventSource = (result.current as any).eventSource;
    if (eventSource) {
      eventSource.simulateMessage(JSON.stringify(mockEvent));
    }

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(mockEvent);
    });
  });

  it('should cleanup EventSource on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useSSE('exec-123', true, vi.fn())
    );

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    const closeSpy = vi.spyOn(
      (result.current as any).eventSource,
      'close'
    );

    unmount();

    expect(closeSpy).toHaveBeenCalled();
  });

  it('should handle connection errors', async () => {
    const { result } = renderHook(() =>
      useSSE('exec-123', true, vi.fn())
    );

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Simulate error
    const eventSource = (result.current as any).eventSource;
    if (eventSource && eventSource.onerror) {
      eventSource.readyState = 2; // CLOSED
      eventSource.onerror(new Event('error'));
    }

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).not.toBeNull();
    });
  });

  it('should not connect when execId is empty', () => {
    const { result } = renderHook(() =>
      useSSE('', true, vi.fn())
    );

    expect(result.current.isConnected).toBe(false);
  });

  it('should reconnect when execId changes', async () => {
    const { result, rerender } = renderHook(
      ({ execId }) => useSSE(execId, true, vi.fn()),
      { initialProps: { execId: 'exec-123' } }
    );

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Change execId
    rerender({ execId: 'exec-456' });

    // Should reconnect
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });
});
