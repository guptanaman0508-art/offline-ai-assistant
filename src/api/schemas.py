"""
Pydantic Request and Response Schemas for the Offline AI Assistant FastAPI Backend.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Backend operational status, e.g. 'ok'")
    ollama_reachable: bool = Field(..., description="Whether local Ollama daemon is reachable")
    ollama_host: str = Field(..., description="Host URI of the Ollama server")


class ModelsResponse(BaseModel):
    """List of locally available Ollama models."""
    models: List[str] = Field(..., description="List of model tags installed locally in Ollama")
    count: int = Field(..., description="Number of models installed")


class ChatRequest(BaseModel):
    """Chat message request schema."""
    message: str = Field(..., min_length=1, description="User prompt text")
    model: Optional[str] = Field(None, description="Optional Ollama model tag. Defaults to llama3.2:3b")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation isolation")


class ChatResponse(BaseModel):
    """Chat message response schema."""
    session_id: str = Field(..., description="Active session ID for continuing conversation")
    model: str = Field(..., description="Model tag that answered the request")
    response: str = Field(..., description="Model generated response text")
    latency_seconds: float = Field(..., description="Turnaround latency in seconds")


class ClearHistoryRequest(BaseModel):
    """Optional payload when deleting history for a specific session."""
    session_id: Optional[str] = Field(None, description="Specific session ID to clear; if omitted, clears all")


class ClearHistoryResponse(BaseModel):
    """Response confirming conversation history clearance."""
    cleared: bool = Field(..., description="Whether history was cleared successfully")
    session_id: Optional[str] = Field(None, description="The session ID that was cleared, or null if all cleared")
    message: str = Field(..., description="Status summary message")


class MetricsResponse(BaseModel):
    """System hardware and Ollama daemon memory metrics."""
    system: Dict[str, Any] = Field(..., description="Host OS, CPU, and physical RAM hardware details")
    ollama_rss_mb: Optional[float] = Field(None, description="Current Ollama background daemon RAM in MB")
