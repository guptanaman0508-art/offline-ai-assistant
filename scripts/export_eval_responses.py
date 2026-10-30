#!/usr/bin/env python3
"""
Standalone Utility: Export Complete Model Answers for Manual Evaluation.

Exports the complete, untruncated answers for all 5 prompts from each of the 3 models
(llama3.2:3b, qwen2.5:3b, mistral:latest) to `results/full_responses_for_eval.json`.

Preserves raw benchmark files (raw_runs.csv, summary.csv, human_eval_scores.csv)
without modification.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Ensure project root is in sys.path when running as `python scripts/export_eval_responses.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ollama_client import OllamaClient
from src.benchmark import load_benchmark_prompts

TARGET_MODELS = [
    "llama3.2:3b",
    "qwen2.5:3b",
    "mistral:latest",
]

PROMPTS_FILE = PROJECT_ROOT / "data" / "benchmark_prompts.json"
OUTPUT_FILE = PROJECT_ROOT / "results" / "full_responses_for_eval.json"


def export_full_responses() -> None:
    print("=" * 75)
    print("   Offline AI Assistant - Full Evaluation Responses Exporter   ")
    print("=" * 75)
    print("WARNING: These responses will be newly generated for quality scoring")
    print("and are not necessarily the exact runs captured during previous speed benchmarks.")
    print("=" * 75)

    client = OllamaClient()

    # Verify Ollama server connectivity
    if not client.is_server_online():
        print(f"\n[ERROR] Local Ollama server is offline at {client.host or 'http://localhost:11434'}.")
        print("Please ensure Ollama is running (`ollama serve`) and try again.\n")
        sys.exit(1)

    # Load the exact 5 prompts and reference key points
    prompts = load_benchmark_prompts(PROMPTS_FILE)
    print(f"\nLoaded {len(prompts)} prompts from: {PROMPTS_FILE.relative_to(PROJECT_ROOT)}")

    export_records: List[Dict[str, Any]] = []

    for model_name in TARGET_MODELS:
        print(f"\n>>> Model: {model_name}")

        # Check availability before querying
        if not client.is_model_available(model_name):
            print(f"  [ERROR] Model '{model_name}' is not installed locally in Ollama.")
            print(f"  Run `ollama pull {model_name}` first.\n")
            # Record failed availability explicitly without inventing responses
            for p in prompts:
                export_records.append({
                    "model_name": model_name,
                    "prompt_id": p.get("id", "unknown"),
                    "prompt_text": p.get("prompt", ""),
                    "reference_key_points": p.get("reference_key_points", []),
                    "full_response": None,
                    "status": "FAILED",
                    "error_message": f"Model '{model_name}' is not installed locally in Ollama.",
                    "timestamp": datetime.now().isoformat(),
                })
            continue

        for p in prompts:
            prompt_id = p.get("id", "unknown")
            prompt_text = p.get("prompt", "")
            key_points = p.get("reference_key_points", [])

            print(f"  Generating response for [{prompt_id}]... ", end="", flush=True)

            timestamp = datetime.now().isoformat()
            try:
                # Query model with temperature 0 for deterministic, reproducible generation
                messages = [{"role": "user", "content": prompt_text}]
                res = client.chat(
                    messages=messages,
                    model_name=model_name,
                    options={"temperature": 0.0},
                )

                full_text = res.get("content", "")
                latency = res.get("latency_seconds", 0.0)

                export_records.append({
                    "model_name": model_name,
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "reference_key_points": key_points,
                    "full_response": full_text,
                    "status": "SUCCESS",
                    "error_message": "",
                    "latency_seconds": round(latency, 3),
                    "timestamp": timestamp,
                })
                print(f"DONE ({round(latency, 2)}s, {len(full_text)} chars)")

            except Exception as e:
                print(f"FAILED ({e})")
                export_records.append({
                    "model_name": model_name,
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "reference_key_points": key_points,
                    "full_response": None,
                    "status": "FAILED",
                    "error_message": str(e),
                    "timestamp": timestamp,
                })

    # Ensure results directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(export_records, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 75)
    print(f"Full untruncated answers successfully exported to:\n  -> {OUTPUT_FILE}")
    print("Next Step: Use data/EVALUATION_RUBRIC.md to evaluate these answers")
    print("and fill in results/human_eval_scores.csv.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    export_full_responses()
