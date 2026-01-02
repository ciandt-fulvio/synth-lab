"""
Chat API router for synth-lab.

REST endpoint for post-interview chat with synths.

References:
    - Chat Service: src/synth_lab/services/chat/service.py
    - Contract: specs/015-synth-chat/contracts/chat-api.yaml
"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from synth_lab.models.chat import ChatRequest, ChatResponse
from synth_lab.repositories.synth_repository import SynthNotFoundError
from synth_lab.services.chat.service import ChatService

router = APIRouter()


def get_chat_service() -> ChatService:
    """Get chat service instance."""
    return ChatService()


@router.post("/{synth_id}/chat", response_model=ChatResponse)
async def chat_with_synth(synth_id: str, request: ChatRequest) -> ChatResponse:
    """
    Send a message to a synth and receive their response.

    Continues a conversation with a synth after an interview, maintaining
    context from the interview and previous chat messages.

    Args:
        synth_id: The ID of the synth to chat with.
        request: Chat request containing message and history.

    Returns:
        ChatResponse with the synth's response message.

    Raises:
        404: If synth not found.
        422: If request validation fails.
    """
    service = get_chat_service()

    try:
        return service.generate_response(synth_id, request)
    except SynthNotFoundError:
        raise HTTPException(status_code=404, detail=f"Synth {synth_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{synth_id}/chat/stream")
async def chat_with_synth_stream(synth_id: str, request: ChatRequest) -> StreamingResponse:
    """
    Send a message to a synth and receive a streaming response.

    Returns real-time token-by-token response via Server-Sent Events.
    Each chunk is sent as a 'data:' SSE event.

    Args:
        synth_id: The ID of the synth to chat with.
        request: Chat request containing message and history.

    Returns:
        StreamingResponse with text/event-stream content type.

    Raises:
        404: If synth not found.
        422: If request validation fails.

    Usage:
        ```javascript
        const response = await fetch('/api/synths/{synth_id}/chat/stream', {
          method: 'POST',
          body: JSON.stringify(request),
        });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          // Parse SSE: lines starting with 'data: '
        }
        ```
    """
    service = get_chat_service()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            for chunk in service.generate_response_stream(synth_id, request):
                # Send each chunk as an SSE data event
                yield f"data: {chunk}\n\n"
            # Signal end of stream
            yield "data: [DONE]\n\n"
        except SynthNotFoundError:
            yield f"data: [ERROR] Synth {synth_id} not found\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        })
