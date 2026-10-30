"""
FastAPI Backend Application Entry Point for Offline AI Assistant.

Provides local REST API endpoints for:
- Health check & Ollama availability (`GET /health`)
- Installed model discovery (`GET /models`)
- Multi-turn conversation chat with isolated session IDs (`POST /chat`)
- Conversation history clearance (`DELETE /chat/history`)
- Host hardware and process memory inspection (`GET /metrics`)

CORS is configured to enable seamless local frontend development (including Vite default localhost origins).
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.ollama_client import OllamaClient
from src.metrics import get_hardware_info, get_ollama_memory_mb
from src.api.session_manager import SessionManager
from src.api.schemas import (
    HealthResponse,
    ModelsResponse,
    ChatRequest,
    ChatResponse,
    ClearHistoryResponse,
    MetricsResponse,
)

app = FastAPI(
    title="Offline AI Assistant Backend API",
    description=(
        "Local, privacy-focused REST API powering the Offline AI Assistant. "
        "Interacts exclusively with on-device Ollama models."
    ),
    version="1.0.0",
)

# Configure CORS for local development (supports Vite default ports 5173, 3000, etc.)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared instances for the FastAPI app lifecycle
ollama_client = OllamaClient()
session_manager = SessionManager()


def get_ollama_client() -> OllamaClient:
    """Dependency getter for OllamaClient (enables clean testing dependency overrides)."""
    return ollama_client


def get_session_manager() -> SessionManager:
    """Dependency getter for SessionManager (enables clean testing dependency overrides)."""
    return session_manager


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Backend Health & Ollama Status",
    tags=["System"],
)
def get_health(client: OllamaClient = Depends(get_ollama_client)) -> HealthResponse:
    """
    Check backend operational status and verify that the local Ollama daemon is reachable.
    """
    reachable = client.is_server_online()
    return HealthResponse(
        status="ok",
        ollama_reachable=reachable,
        ollama_host=client.host or "http://localhost:11434",
    )


@app.get(
    "/models",
    response_model=ModelsResponse,
    summary="List Local Models",
    tags=["Models"],
)
def get_models(client: OllamaClient = Depends(get_ollama_client)) -> ModelsResponse:
    """
    Retrieve the list of locally available models currently downloaded in Ollama.
    """
    try:
        models = client.list_local_models()
        return ModelsResponse(models=models, count=len(models))
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Cannot connect to local Ollama server at {client.host or 'http://localhost:11434'}. "
                "Ensure Ollama is running (`ollama serve`)."
            ),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query local models: {str(e)}",
        ) from e


@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send Chat Message",
    tags=["Chat"],
)
def post_chat(
    request: ChatRequest,
    client: OllamaClient = Depends(get_ollama_client),
    sessions: SessionManager = Depends(get_session_manager),
) -> ChatResponse:
    """
    Process a chat message using the specified local Ollama model.
    Maintains multi-turn context isolated by session ID.
    """


    user_text = request.message.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty.",
        )

    # 1. Resolve or generate session ID
    session_id = sessions.get_or_create_session(request.session_id)

    # 2. Resolve model name (fallback to client default)
    selected_model = request.model or client.model_name

    # 3. Check server connectivity
    if not client.is_server_online():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama daemon is not reachable at http://localhost:11434.",
        )

    # 4. Check model availability
    try:
        if not client.is_model_available(selected_model):
            available = client.list_local_models()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Model '{selected_model}' is not installed locally. "
                    f"Available models: {available}. Run: ollama pull {selected_model}"
                ),
            )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Connection error to Ollama server: {str(e)}",
        ) from e

    # 5. Retrieve current session history and append user message
    sessions.add_message(session_id, role="user", content=user_text)
    history = sessions.get_history(session_id)

    # 6. Execute chat inference
    try:
        result = client.chat(messages=history, model_name=selected_model)
        assistant_reply = result.get("content", "")
        latency = result.get("latency_seconds", 0.0)

        # Append assistant reply to session history for future multi-turn turns
        sessions.add_message(session_id, role="assistant", content=assistant_reply)

        return ChatResponse(
            session_id=session_id,
            model=selected_model,
            response=assistant_reply,
            latency_seconds=round(latency, 3),
        )

    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error with model '{selected_model}': {str(e)}",
        ) from e


@app.delete(
    "/chat/history",
    response_model=ClearHistoryResponse,
    summary="Clear Chat History",
    tags=["Chat"],
)
def delete_chat_history(
    session_id: Optional[str] = Query(None, description="Optional session ID to clear"),
    sessions: SessionManager = Depends(get_session_manager),
) -> ClearHistoryResponse:
    """
    Clear conversation history.
    - If `session_id` is supplied, resets only that session back to the default system prompt.
    - If omitted, clears all active session histories from memory.
    """

    if session_id:
        cleared = sessions.clear_history(session_id)
        if not cleared:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session ID '{session_id}' not found.",
            )
        return ClearHistoryResponse(
            cleared=True,
            session_id=session_id,
            message=f"Conversation history for session '{session_id}' was reset.",
        )
    
    sessions.clear_history(None)
    return ClearHistoryResponse(
        cleared=True,
        session_id=None,
        message="All active session histories have been cleared.",
    )


@app.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="System and Ollama Metrics",
    tags=["System"],
)
def get_metrics() -> MetricsResponse:
    """
    Retrieve real-time host hardware information and Ollama process resident memory (RSS in MB).
    """
    hw_info = get_hardware_info()
    ollama_mem = get_ollama_memory_mb()
    return MetricsResponse(
        system=hw_info,
        ollama_rss_mb=ollama_mem,
    )
