from fastapi import Request, HTTPException, status
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import logging
from utils.llm import LLM

# Updated imports for modern LangChain
from langchain_google_firestore import FirestoreChatMessageHistory
from firebase_admin import firestore
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# Setup logging
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.firestore_client = firestore.client()
        
        # Create a reusable chat prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant."), 
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create the base runnable chain
        llm = LLM().get_openai_model()
        self.base_chain = self.prompt | llm | StrOutputParser()

    def get_session(self, session_id, user_id):
        cache_key = f"{user_id}:{session_id}"
        if cache_key not in self.sessions:
            # Create the runnable with message history
            chain_with_history = RunnableWithMessageHistory(
                self.base_chain,
                lambda session_id: self.get_chat_history(user_id, session_id),
                input_messages_key="input",
                history_messages_key="history"
            )
            self.sessions[cache_key] = chain_with_history
        
        return self.sessions[cache_key]
    
    def add_sessionid_to_sessions(self, session_id, user_id):
        cache_key = f"{user_id}:{session_id}"
        if cache_key not in self.sessions:
            # Create the runnable with message history
            chain_with_history = RunnableWithMessageHistory(
                self.base_chain,
                lambda session_id: self.get_chat_history(user_id, session_id),
                input_messages_key="input",
                history_messages_key="history"
            )
            self.sessions[cache_key] = chain_with_history
        
    
    def get_chat_history(self, user_id, session_id):
        """Get a FirestoreChatMessageHistory for the specified user and session"""
        collection_path = f"users/{user_id}/chat_sessions"
        return CustomFirestoreChatHistory(
            user_id=user_id,
            session_id=session_id,
            client=self.firestore_client
        )
        
    def create_session(self, user_id, session_id, name=None):
        """Create a new session in Firestore"""
        now = datetime.now().isoformat()
        session_name = name or f"Chat {now}"
        
        # Create session document
        self.firestore_client.collection("users").document(user_id).collection("chat_sessions").document(session_id).set({
            "name": session_name,
            "created_at": now,
            "updated_at": now,
            "messages": []
        })
        self.add_sessionid_to_sessions(session_id, user_id)
        
        return session_id

    def list_user_sessions(self, user_id):
        """List all sessions for a specific user"""
        sessions = self.firestore_client.collection("users").document(user_id).collection("chat_sessions").stream()
        result = []
        
        for session in sessions:
            session_data = session.to_dict()
            session_data["id"] = session.id
            self.add_sessionid_to_sessions(session.id, user_id)
            result.append(session_data)
            
        return result
    
    def check_session_exists(self, user_id, session_id):
        """Check if a session exists for a specific user"""
        cache_key = f"{user_id}:{session_id}"
        in_memory = cache_key in self.sessions
        return in_memory        

# Add this custom chat history class
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory

class CustomFirestoreChatHistory(BaseChatMessageHistory):
    def __init__(self, user_id, session_id, client):
        self.user_id = user_id
        self.session_id = session_id
        self.client = client
        self.doc_ref = client.collection("users").document(user_id).collection("chat_sessions").document(session_id)
    
    def add_messages(self, messages):
        for message in messages:
            self.add_message(message)
    
    def add_message(self, message):
        # Convert message to a plain dict
        if isinstance(message, HumanMessage):
            message_dict = {
                "type": "human",
                "content": message.content,
                "timestamp": datetime.now().isoformat()
            }
        elif isinstance(message, AIMessage):
            message_dict = {
                "type": "ai",
                "content": message.content,
                "timestamp": datetime.now().isoformat()
            }
        elif isinstance(message, SystemMessage):
            message_dict = {
                "type": "system",
                "content": message.content,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")
        
        # Add the message to Firestore
        self.doc_ref.update({
            "messages": firestore.ArrayUnion([message_dict]),
            "updated_at": datetime.now().isoformat()
        })
    
    def clear(self):
        self.doc_ref.update({
            "messages": [],
            "updated_at": datetime.now().isoformat()
        })
    
    @property
    def messages(self):
        # Get the document
        doc = self.doc_ref.get()
        if not doc.exists:
            return []
        
        # Extract messages
        data = doc.to_dict()
        messages_data = data.get("messages", [])
        
        # Convert to LangChain message objects
        result = []
        for msg in messages_data:
            if msg["type"] == "human":
                result.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                result.append(AIMessage(content=msg["content"]))
            elif msg["type"] == "system":
                result.append(SystemMessage(content=msg["content"]))
        
        return result

# Initialize globally
session_manager = SessionManager()

async def get_user_sessions(user_id: str, request: Request):
    """Get all chat sessions for a user"""
    try:
        sessions = session_manager.list_user_sessions(user_id)
        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )

async def process_chat_message(user_id: str, message: str, session_id: Optional[str], request: Request):
    """Process a chat message using the specified session or create a new one"""
    try:
        
        if session_id and not session_manager.check_session_exists(user_id, session_id):
            # If session exists, check if it's active
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session is not available" 
            )
            
        if not session_id:
            # Create a new session if none specified
            session_id = str(uuid.uuid4())
            session_manager.create_session(user_id, session_id)
            
        # Get the runnable with message history
        chain = session_manager.get_session(session_id, user_id)
        
        # Process the message with session context
        response = await chain.ainvoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Update the session's last updated timestamp
        now = datetime.now().isoformat()
        try:
            session_manager.firestore_client.collection("users").document(user_id).collection("chat_sessions").document(session_id).update({
                "updated_at": now
            })
        except Exception as e:
            logger.warning(f"Failed to update session timestamp: {str(e)}")
        
        return {
            "status": "success",
            "message": response,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


async def delete_user_session(user_id: str, session_id: str, request: Request):
    """Delete a specific chat session for a user"""
    try:
        # Check if session exists
        sessions = session_manager.list_user_sessions(user_id)
        session_exists = any(s["id"] == session_id for s in sessions)
        
        if not session_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        # Delete the session from Firestore
        session_manager.firestore_client.collection("users").document(user_id).collection("chat_sessions").document(session_id).delete()
        
        # Remove from cache if present
        cache_key = f"{user_id}:{session_id}"
        if cache_key in session_manager.sessions:
            del session_manager.sessions[cache_key]
        
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )