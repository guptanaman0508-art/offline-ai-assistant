"""
Pydantic Schemas for Structured Assistant Responses.

Defines the contract for structured outputs received from the local Ollama LLMs.
Uses Pydantic v2 for data parsing and validation.
"""

from typing import List
from pydantic import BaseModel, Field


class StructuredAssistantResponse(BaseModel):
    """
    Schema for structured assistant responses.
    
    Fields:
    - answer: The main explanatory response text.
    - key_points: List of bullet-point summary items extracted from the answer.
    """
    answer: str = Field(
        ...,
        min_length=1,
        description="The primary explanation or answer text provided by the model."
    )
    key_points: List[str] = Field(
        ...,
        min_length=1,
        description="List of key points or takeaway summary statements."
    )
