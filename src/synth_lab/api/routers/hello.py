"""
Hello World router for testing auto-update-docs system.

Simple test endpoint to validate documentation automation.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(prefix="/hello", tags=["testing"])


@router.get("")
def hello_world():
    """
    Hello World endpoint.

    Returns a simple greeting message.

    Returns:
        dict: Message with greeting and timestamp
    """
    return {
        "message": "Hello, World!",
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "ok"
    }


@router.get("/{name}")
def hello_name(name: str):
    """
    Personalized greeting endpoint.

    Args:
        name: Name to greet

    Returns:
        dict: Personalized greeting message with status
    """
    return {
        "message": f"Hello, {name}!",
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "personalized"
    }
