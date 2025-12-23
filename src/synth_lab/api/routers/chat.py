"""
Chat API router for synth-lab.

REST endpoint for post-interview chat with synths.

References:
    - Chat Service: src/synth_lab/services/chat/service.py
    - Contract: specs/015-synth-chat/contracts/chat-api.yaml
"""

from fastapi import APIRouter, HTTPException

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
