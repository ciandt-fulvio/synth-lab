"""
Chat models for synth conversation after interview.

Pydantic models for chat request/response validation.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageModel(BaseModel):
    """Individual message in chat conversation."""

    role: Literal["user", "synth"]
    content: str = Field(..., min_length=1)
    timestamp: datetime


class ChatRequest(BaseModel):
    """Request to send a message to a synth."""

    exec_id: str = Field(..., description="Execution ID of the interview")
    message: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[ChatMessageModel] = Field(
        default_factory=list,
        description="Previous messages in this chat session",
    )


class ChatResponse(BaseModel):
    """Response from synth in chat."""

    message: str
    timestamp: datetime
