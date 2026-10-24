"""
Command-line Chatbot application for Offline AI Assistant.

Provides an interactive CLI interface with:
- Configurable model selection
- Clean exit handling
- Response latency measurement
- Input validation and graceful error recovery
"""

import sys
import argparse
from typing import List, Dict

# Support running directly via `python src/app.py` or as a module
try:
    from src.ollama_client import OllamaClient
except ImportError:
    from ollama_client import OllamaClient


def display_welcome_banner(model_name: str) -> None:
    """Print welcome header and usage instructions."""
    print("=" * 60)
    print("   Offline AI Assistant - Command-Line Chatbot (Phase 1)   ")
    print("=" * 60)
    print(f"Active Model  : {model_name}")
    print("Inference     : 100% Local (via Ollama)")
    print("Exit commands : Type 'exit', 'quit', or '/bye' to leave")
    print("Clear history : Type 'clear' to start a new conversation")
    print("-" * 60)


def main() -> None:
    """Main loop for the interactive terminal chat."""
    parser = argparse.ArgumentParser(
        description="Run local offline AI assistant chatbot with Ollama."
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="llama3.2:3b",
        help="Ollama model tag to use (default: llama3.2:3b)",
    )
    args = parser.parse_args()

    client = OllamaClient(model_name=args.model)

    # 1. Check if Ollama daemon is running
    if not client.is_server_online():
        print("\n[ERROR] Ollama server is not running or not responding at http://localhost:11434.")
        print("Please start Ollama in your terminal using:")
        print("    ollama serve")
        print("or open the Ollama desktop application.\n")
        sys.exit(1)

    # 2. Check if the specified model is installed
    try:
        available_models = client.list_local_models()
        if not available_models:
            print(f"\n[WARNING] No local models are currently installed in Ollama.")
            print(f"To download your first model, open a terminal and run:")
            print(f"    ollama pull {args.model}")
            print("Then re-run this application.\n")
            sys.exit(1)

        if not client.is_model_available(args.model):
            print(f"\n[ERROR] Target model '{args.model}' is not available locally.")
            print("Installed models found:")
            for m in available_models:
                print(f"  - {m}")
            print(f"\nYou can pull it using: ollama pull {args.model}")
            print(f"Or run with an installed model: python src/app.py --model {available_models[0]}\n")
            sys.exit(1)
    except ConnectionError as err:
        print(f"\n[ERROR] {err}\n")
        sys.exit(1)

    display_welcome_banner(args.model)

    # Conversation history list for multi-turn context
    conversation_history: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful, accurate, and concise offline study and notes assistant. "
                "Provide clear explanations and structured answers."
            ),
        }
    ]

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ("exit", "quit", "/bye", ":q"):
                print("\nAssistant: Goodbye! Have a productive study session.\n")
                break

            # Check for reset command
            if user_input.lower() == "clear":
                conversation_history = [conversation_history[0]]
                print("\n[System] Conversation history cleared.")
                continue

            # Append user message
            conversation_history.append({"role": "user", "content": user_input})

            print("\nAssistant: (thinking locally...)", end="\r", flush=True)

            # Query the model
            result = client.chat(messages=conversation_history)

            assistant_reply = result["content"]
            latency = result["latency_seconds"]

            # Clear temporary status line
            print(" " * 40, end="\r")

            print(f"Assistant: {assistant_reply}")
            print(f"\n[⏱️ Latency: {latency:.2f}s | Model: {args.model}]")

            # Append assistant response to history
            conversation_history.append({"role": "assistant", "content": assistant_reply})

        except KeyboardInterrupt:
            # Handle Ctrl+C cleanly
            print("\n\nSession interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] Request failed: {e}")
            print("You can try another question, or check if Ollama is running.")


if __name__ == "__main__":
    main()
