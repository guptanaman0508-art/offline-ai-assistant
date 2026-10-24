"""
Metrics and System Resource Measurement Module for Model Benchmark.

Measures:
- Latency (high-resolution wall clock timer)
- Tokens generated and token speed (tokens per second) from Ollama metadata
- Ollama process memory (RSS in MB via psutil)
- System unified memory stats
"""

import os
import platform
import psutil
from typing import Any, Dict, Optional, Tuple


def get_hardware_info() -> Dict[str, Any]:
    """
    Capture system hardware and OS environment details for reproducibility.
    Does not guess or invent data.
    """
    mem = psutil.virtual_memory()
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": round(mem.total / (1024 ** 3), 2),
        "available_ram_gb": round(mem.available / (1024 ** 3), 2),
    }


def get_ollama_memory_mb() -> Optional[float]:
    """
    Inspect the memory usage (Resident Set Size in Megabytes) of the active Ollama daemon.
    
    Returns total RSS in MB across Ollama background processes, or None if Ollama process
    cannot be inspected.
    """
    total_rss_bytes = 0
    found_ollama = False

    for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
        try:
            name = (proc.info["name"] or "").lower()
            cmdline = " ".join(proc.info["cmdline"] or []).lower()

            # Ignore our own python benchmark runner process
            if "python" in name:
                continue

            # Identify Ollama server process
            if "ollama" in name or "ollama" in cmdline:
                mem_info = proc.info.get("memory_info")
                if mem_info and hasattr(mem_info, "rss"):
                    total_rss_bytes += mem_info.rss
                    found_ollama = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if found_ollama:
        return round(total_rss_bytes / (1024 * 1024), 2)
    return None


def extract_generation_metrics(raw_response: Any) -> Dict[str, Optional[float]]:
    """
    Extract token counts, load duration, and tokens per second from the native Ollama response.
    
    Ollama returns duration timestamps in nanoseconds:
    - total_duration: total time spent in Ollama
    - load_duration: time spent loading the model into memory
    - prompt_eval_count: tokens in prompt
    - prompt_eval_duration: time spent processing prompt
    - eval_count: number of tokens generated in response
    - eval_duration: time spent generating tokens
    """
    # Accommodate object or dict attributes
    def _get(attr: str) -> Optional[int]:
        if hasattr(raw_response, attr):
            return getattr(raw_response, attr)
        if isinstance(raw_response, dict):
            return raw_response.get(attr)
        return None

    eval_count = _get("eval_count")
    eval_duration_ns = _get("eval_duration")
    load_duration_ns = _get("load_duration")
    prompt_eval_count = _get("prompt_eval_count")
    prompt_eval_duration_ns = _get("prompt_eval_duration")

    eval_duration_s = (eval_duration_ns / 1e9) if eval_duration_ns else None
    load_duration_s = (load_duration_ns / 1e9) if load_duration_ns else None
    prompt_eval_duration_s = (prompt_eval_duration_ns / 1e9) if prompt_eval_duration_ns else None

    # Calculate tokens per second reliably if both token count and duration are present
    tokens_per_second: Optional[float] = None
    if eval_count is not None and eval_duration_s and eval_duration_s > 0:
        tokens_per_second = round(eval_count / eval_duration_s, 2)

    return {
        "eval_count": eval_count,
        "eval_duration_s": round(eval_duration_s, 3) if eval_duration_s else None,
        "load_duration_s": round(load_duration_s, 3) if load_duration_s else None,
        "prompt_eval_count": prompt_eval_count,
        "prompt_eval_duration_s": round(prompt_eval_duration_s, 3) if prompt_eval_duration_s else None,
        "tokens_per_second": tokens_per_second,
    }
