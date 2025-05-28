from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from services.auth_service import verify_token
from models.chatbot_model import ChatSession, ChatRequest, ChatMessage
import logging

# Import the service that will be implemented later
from services.chatbot_service import (
    get_user_sessions,
    process_chat_message,
    delete_user_session  # Add this import
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot")


@router.get("/sessions", response_model=List[ChatSession])
async def get_sessions(request: Request):
    """
    Get a list of all available sessions (active and inactive) for the current user.
    """
    try:
        user_id = request.state.user["uid"]
        sessions = await get_user_sessions(user_id=user_id, request=request)
        return JSONResponse(content=sessions, status_code=200)
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, request: Request):
    """
    Delete a specific chat session by its ID.
    """
    try:
        user_id = request.state.user["uid"]
        result = await delete_user_session(user_id=user_id, session_id=session_id, request=request)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post("/chat")
async def chat(
    chat_request: ChatRequest, 
    request: Request, 
):
    """
    Send a message and receive a response using the active session's ConversationChain.
    If no session is active or specified, creates a new session.
    """
    try:
        user_id = request.state.user["uid"]
        result = await process_chat_message(
            user_id=user_id,
            message=chat_request.message,
            session_id=chat_request.session_id,
            request=request
        )
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )