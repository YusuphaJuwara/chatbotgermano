# models.py
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
import datetime
import uuid
from cohere.types.chat_citation import ChatCitation

class DocIdsRequest(BaseModel):
    # TODO: Delete later
    doc_ids: List[str]

# --- Citation Models ---
class CitationBase(BaseModel):
    id: int = Field(..., description="Unique identifier for the citation (e.g., '0', '3')")
    msg_id: int = Field(..., description="ID of the message associated with this citation") 
    doc_ids: List[str] = Field(..., description="List of document IDs associated with this citation")
    text: str = Field(..., description="Content of the cited document")
    start: Optional[int] = Field(None, description="Start index of the citation in the document text")
    end: Optional[int] = Field(None, description="End index of the citation in the document text")
    
    class Config:
        from_attributes = True # Enable ORM mode

class CitationResponse(CitationBase):
    # Fields returned in API responses for citations
    class Config:
        from_attributes = True # Enable ORM mode

# --- Base Models ---
class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender ('user' or 'assistant')")
    content: str = Field(..., description="The text content of the message")
    link: Optional[str] = Field(None, description="Optional URL associated with the message")

class MessageCreate(MessageBase):
    # Fields required to create a new message (sent in request body)
    ai_model: Optional[str] = Field(None, description="Identifier for the AI model used (if assistant)")

class MessageResponse(MessageBase):
    # Fields returned in API responses for messages
    id: int
    session_id: str
    timestamp: datetime.datetime
    ai_model: Optional[str] = None # Include ai_model in response
    citations: List[CitationBase] = [] # List of citations associated with the message
    # documents: List[Dict] = [] # List of documents associated with the message

    class Config:
        from_attributes = True # Enable ORM mode for SQLAlchemy model conversion

# --- Chat Session Models ---
class ChatSessionBase(BaseModel):
    title: str = Field(..., description="Title of the chat session")

class ChatSessionCreate(BaseModel):
    # Optional title when creating a session
    title: Optional[str] = Field(None, description="Optional initial title for the chat session")

class ChatSessionResponse(ChatSessionBase):
    # Fields returned in API responses for chat sessions
    id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True # Enable ORM mode
