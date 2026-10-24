"""
Model Benchmark Runner.

Executes a reproducible benchmark comparing three local Ollama models on:
- Response latency (total wall clock time)
- Cold-start vs warm runs (warm-up phase separated)
- Token generation speed (eval_tokens / second from Ollama native counters)
- Ollama process memory consumption (RSS in MB)
- Structured output reliability:
  * First-attempt validity
  * Bounded retry success rate (within max 3 attempts)
  * Average attempts used
  * Error categorization (invalid_json, missing_field, type_error, etc.)

Outputs:
- results/raw_runs.csv: Granular metrics per prompt and run type (warmup vs measured)
- results/summary.csv: Aggregated statistics (median latency, token rate, memory, structured reliability)
"""

import os
import sys
import csv
import json
import time
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Support direct and module imports
try:
    from src.ollama_client import OllamaClient
    from src.metrics import get_hardware_info, get_ollama_memory_mb, extract_generation_metrics
    from src.schemas import StructuredAssistantResponse
    from src.evaluation import run_bounded_retry_structured_call, ErrorCategory
except ImportError:
    from ollama_client import OllamaClient
    from metrics import get_hardware_info, get_ollama_memory_mb, extract_generation_metrics
    from schemas import StructuredAssistantResponse
    from evaluation import run_bounded_retry_structured_call, ErrorCategory


DEFAULT_PROMPTS_FILE = Path(__file__).resolve().parent.parent / "data" / "benchmark_prompts.json"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
RAW_RESULTS_CSV = RESULTS_DIR / "raw_runs.csv"
SUMMARY_RESULTS_CSV = RESULTS_DIR / "summary.csv"


RAW_CSV_HEADERS = [
    "run_id",
    "timestamp",
    "model_name",
    "prompt_id",
    "category",
    "run_type",  # 'cold_warmup' or 'measured'
    "trial_number",
    "status",  # 'SUCCESS' or 'FAILED'
    "error_category",
    "error_message",
    "attempts_used",
    "structured_valid_first_try",
    "structured_valid_final",
    "latency_seconds",
    "load_duration_s",
    "eval_tokens",
    "eval_duration_s",
    "tokens_per_second",
    "baseline_ram_mb",
    "peak_ram_mb",
    "response_preview",
    "quality_score",  # Evaluated according to rubric; never invented
]

SUMMARY_CSV_HEADERS = [
    "model_name",
    "total_trials",
    "successful_trials",
    "failed_trials",
    "success_rate_pct",
    "first_attempt_valid_pct",
    "final_valid_pct",
    "avg_attempts_used",
    "median_latency_s",
    "min_latency_s",
    "max_latency_s",
    "avg_tokens_per_second",
    "cold_start_load_s",
    "avg_peak_ram_mb",
    "status_notes",
]


def load_benchmark_prompts(prompts_path: Path) -> List[Dict[str, Any]]:
    """Load the fixed list of prompts from the JSON dataset."""
    if not prompts_path.exists():
        raise FileNotFoundError(f"Prompts file not found at: {prompts_path}")
    with open(prompts_path, "r", encoding="utf-8") as f:
        return json.load(f)


def initialize_results_dir() -> None:
    """Ensure the results folder exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def append_raw_run_to_csv(row: Dict[str, Any], filepath: Path) -> None:
    """Append a single run record to the raw results CSV file."""
    file_exists = filepath.exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def execute_single_prompt(
    client: OllamaClient,
    model_name: str,
    prompt_item: Dict[str, Any],
    run_type: str,
    trial_number: int,
    structured: bool = False,
) -> Dict[str, Any]:
    """
    Execute a single prompt against the specified model, capturing metrics and handling failures.
    If structured is True, uses bounded retries (up to 3 attempts) and validates with Pydantic.
    """
    prompt_id = prompt_item.get("id", "unknown")
    category = prompt_item.get("category", "general")
    prompt_text = prompt_item.get("prompt", "")

    timestamp = datetime.now().isoformat()
    run_id = f"{model_name}_{prompt_id}_{run_type}_{trial_number}_{int(time.time())}"

    # Sample memory right before invocation
    baseline_ram = get_ollama_memory_mb()

    record: Dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "model_name": model_name,
        "prompt_id": prompt_id,
        "category": category,
        "run_type": run_type,
        "trial_number": trial_number,
        "status": "FAILED",
        "error_category": "none",
        "error_message": "",
        "attempts_used": 1,
        "structured_valid_first_try": "N/A",
        "structured_valid_final": "N/A",
        "latency_seconds": None,
        "load_duration_s": None,
        "eval_tokens": None,
        "eval_duration_s": None,
        "tokens_per_second": None,
        "baseline_ram_mb": baseline_ram,
        "peak_ram_mb": None,
        "response_preview": "",
        "quality_score": "",  # Unscored until human evaluation against rubric
    }

    try:
        if structured:
            retry_res = run_bounded_retry_structured_call(
                client=client,
                prompt=prompt_text,
                model_name=model_name,
                schema_cls=StructuredAssistantResponse,
                max_attempts=3,
            )
            peak_ram = get_ollama_memory_mb()
            attempts_used = retry_res["attempts_used"]
            success = retry_res["success"]

            first_try_valid = (attempts_used == 1 and success)
            final_valid = success

            preview = ""
            if retry_res["validated_data"]:
                preview = json.dumps(retry_res["validated_data"])[:120]
            elif retry_res["raw_responses"]:
                preview = retry_res["raw_responses"][-1][:120]

            record.update(
                {
                    "status": "SUCCESS" if success else "FAILED",
                    "error_category": retry_res["error_category"],
                    "error_message": retry_res["error_message"],
                    "attempts_used": attempts_used,
                    "structured_valid_first_try": "TRUE" if first_try_valid else "FALSE",
                    "structured_valid_final": "TRUE" if final_valid else "FALSE",
                    "latency_seconds": retry_res["total_latency_seconds"],
                    "peak_ram_mb": peak_ram,
                    "response_preview": preview,
                }
            )
        else:
            messages = [{"role": "user", "content": prompt_text}]
            response_dict = client.chat(messages=messages, model_name=model_name)
            peak_ram = get_ollama_memory_mb()

            raw = response_dict.get("raw_response")
            gen_metrics = extract_generation_metrics(raw)

            content = response_dict.get("content", "").replace("\n", " ")
            preview = (content[:120] + "...") if len(content) > 120 else content

            record.update(
                {
                    "status": "SUCCESS",
                    "latency_seconds": round(response_dict.get("latency_seconds", 0.0), 3),
                    "load_duration_s": gen_metrics.get("load_duration_s"),
                    "eval_tokens": gen_metrics.get("eval_count"),
                    "eval_duration_s": gen_metrics.get("eval_duration_s"),
                    "tokens_per_second": gen_metrics.get("tokens_per_second"),
                    "peak_ram_mb": peak_ram,
                    "response_preview": preview,
                }
            )

    except Exception as e:
        record["error_category"] = "ollama_request_error"
        record["error_message"] = str(e)
        record["peak_ram_mb"] = get_ollama_memory_mb()

    return record


def compute_summary_metrics(raw_records: List[Dict[str, Any]], model_names: List[str]) -> List[Dict[str, Any]]:
    """
    Compute aggregate summary statistics from measured runs only (excluding warmups).
    Includes structured reliability rates alongside latency and token generation speed.
    """
    summary_rows = []

    for model in model_names:
        model_runs = [r for r in raw_records if r["model_name"] == model]
        measured_runs = [r for r in model_runs if r["run_type"] == "measured"]
        cold_runs = [r for r in model_runs if r["run_type"] == "cold_warmup"]

        total_trials = len(measured_runs)
        successful_runs = [r for r in measured_runs if r["status"] == "SUCCESS"]
        failed_runs = [r for r in measured_runs if r["status"] == "FAILED"]

        success_count = len(successful_runs)
        failed_count = len(failed_runs)
        success_rate = round((success_count / total_trials * 100), 1) if total_trials > 0 else 0.0

        latencies = [r["latency_seconds"] for r in successful_runs if r["latency_seconds"] is not None]
        token_rates = [r["tokens_per_second"] for r in successful_runs if r["tokens_per_second"] is not None]
        peak_rams = [r["peak_ram_mb"] for r in successful_runs if r["peak_ram_mb"] is not None]

        # Structured-output metrics
        structured_runs = [r for r in measured_runs if r.get("structured_valid_final") in ("TRUE", "FALSE")]
        first_valid_pct: Optional[float] = None
        final_valid_pct: Optional[float] = None
        avg_attempts: Optional[float] = None

        if structured_runs:
            num_struct = len(structured_runs)
            first_count = sum(1 for r in structured_runs if r.get("structured_valid_first_try") == "TRUE")
            final_count = sum(1 for r in structured_runs if r.get("structured_valid_final") == "TRUE")
            first_valid_pct = round((first_count / num_struct * 100), 1)
            final_valid_pct = round((final_count / num_struct * 100), 1)
            attempts_list = [r["attempts_used"] for r in structured_runs if isinstance(r.get("attempts_used"), int)]
            avg_attempts = round(statistics.mean(attempts_list), 2) if attempts_list else None

        cold_load_s: Optional[float] = None
        for cr in cold_runs:
            if cr.get("load_duration_s"):
                cold_load_s = cr["load_duration_s"]
                break

        median_lat = round(statistics.median(latencies), 3) if latencies else None
        min_lat = round(min(latencies), 3) if latencies else None
        max_lat = round(max(latencies), 3) if latencies else None
        avg_tokens_s = round(statistics.mean(token_rates), 2) if token_rates else None
        avg_ram = round(statistics.mean(peak_rams), 2) if peak_rams else None

        status_notes = "OK"
        if total_trials == 0:
            status_notes = "Model missing or not evaluated"
        elif failed_count > 0:
            status_notes = f"{failed_count} requests failed"

        summary_rows.append(
            {
                "model_name": model,
                "total_trials": total_trials,
                "successful_trials": success_count,
                "failed_trials": failed_count,
                "success_rate_pct": success_rate,
                "first_attempt_valid_pct": first_valid_pct if first_valid_pct is not None else "N/A",
                "final_valid_pct": final_valid_pct if final_valid_pct is not None else "N/A",
                "avg_attempts_used": avg_attempts if avg_attempts is not None else "N/A",
                "median_latency_s": median_lat,
                "min_latency_s": min_lat,
                "max_latency_s": max_lat,
                "avg_tokens_per_second": avg_tokens_s,
                "cold_start_load_s": cold_load_s,
                "avg_peak_ram_mb": avg_ram,
                "status_notes": status_notes,
            }
        )

    return summary_rows


def write_summary_csv(summary_data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save aggregated benchmark comparison to a summary CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_CSV_HEADERS)
        writer.writeheader()
        for row in summary_data:
            writer.writerow(row)


def run_benchmark(
    models: List[str],
    prompts_file: Path = DEFAULT_PROMPTS_FILE,
    trials_per_prompt: int = 1,
    include_warmup: bool = True,
    structured: bool = False,
) -> None:
    """Main benchmark orchestration function."""
    print("=" * 70)
    print("        Offline AI Assistant - Model Benchmark Runner         ")
    print("=" * 70)

    hardware = get_hardware_info()
    print(f"System OS     : {hardware['os']} {hardware['os_release']} ({hardware['architecture']})")
    print(f"CPUs          : {hardware['cpu_count_physical']} physical, {hardware['cpu_count_logical']} logical")
    print(f"System RAM    : {hardware['total_ram_gb']} GB total ({hardware['available_ram_gb']} GB available)")
    print(f"Models Target : {', '.join(models)}")
    print(f"Mode          : {'Structured JSON Output (Pydantic)' if structured else 'Standard Generation'}")
    print("-" * 70)

    initialize_results_dir()
    prompts = load_benchmark_prompts(prompts_file)
    print(f"Loaded {len(prompts)} fixed benchmark prompts from {prompts_file.name}")

    client = OllamaClient()
    if not client.is_server_online():
        print("\n[ERROR] Ollama server is offline. Please run `ollama serve` and retry.\n")
        sys.exit(1)

    installed_models = client.list_local_models()
    print(f"Installed Ollama models detected: {installed_models or 'None'}\n")

    all_raw_records: List[Dict[str, Any]] = []

    for model_name in models:
        print(f"\n>>> Benchmarking Model: {model_name}")

        if not client.is_model_available(model_name):
            print(f"  [SKIPPED] Model '{model_name}' is not downloaded in Ollama.")
            print(f"  To benchmark this model, run in terminal: ollama pull {model_name}")

            fail_record = {
                "run_id": f"{model_name}_unavailable_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "prompt_id": "N/A",
                "category": "availability_check",
                "run_type": "check",
                "trial_number": 0,
                "status": "FAILED",
                "error_category": "ollama_request_error",
                "error_message": f"Model '{model_name}' is not installed locally in Ollama.",
                "attempts_used": 0,
                "structured_valid_first_try": "N/A",
                "structured_valid_final": "N/A",
                "latency_seconds": None,
                "load_duration_s": None,
                "eval_tokens": None,
                "eval_duration_s": None,
                "tokens_per_second": None,
                "baseline_ram_mb": None,
                "peak_ram_mb": None,
                "response_preview": "",
                "quality_score": "",
            }
            append_raw_run_to_csv(fail_record, RAW_RESULTS_CSV)
            all_raw_records.append(fail_record)
            continue

        # 1. Cold-start / Warm-up Run
        if include_warmup and prompts:
            print("  [Warm-up] Executing cold-start run (isolated from final score)...")
            warmup_record = execute_single_prompt(
                client=client,
                model_name=model_name,
                prompt_item=prompts[0],
                run_type="cold_warmup",
                trial_number=0,
                structured=structured,
            )
            append_raw_run_to_csv(warmup_record, RAW_RESULTS_CSV)
            all_raw_records.append(warmup_record)
            if warmup_record["status"] == "SUCCESS":
                print(
                    f"    Warm-up complete: {warmup_record['latency_seconds']}s "
                    f"(load time: {warmup_record['load_duration_s'] or 0.0}s)"
                )
            else:
                print(f"    Warm-up warning: {warmup_record['error_message']}")

        # 2. Measured Trials
        for trial in range(1, trials_per_prompt + 1):
            print(f"  [Trial {trial}/{trials_per_prompt}]")
            for prompt_item in prompts:
                pid = prompt_item["id"]
                print(f"    Prompt: {pid:<25}", end="", flush=True)

                record = execute_single_prompt(
                    client=client,
                    model_name=model_name,
                    prompt_item=prompt_item,
                    run_type="measured",
                    trial_number=trial,
                    structured=structured,
                )
                append_raw_run_to_csv(record, RAW_RESULTS_CSV)
                all_raw_records.append(record)

                if record["status"] == "SUCCESS":
                    if structured:
                        att = record["attempts_used"]
                        print(f"OK ({record['latency_seconds']}s | {att} attempt(s))")
                    else:
                        tps = record["tokens_per_second"]
                        tps_str = f"{tps} tok/s" if tps else "N/A"
                        print(f"OK ({record['latency_seconds']}s | {tps_str})")
                else:
                    print(f"FAILED [{record['error_category']}] ({record['error_message'][:60]})")

    # Generate Summary CSV
    summary_data = compute_summary_metrics(all_raw_records, models)
    write_summary_csv(summary_data, SUMMARY_RESULTS_CSV)

    print("\n" + "=" * 70)
    print("                     BENCHMARK SUMMARY RESULTS                     ")
    print("=" * 70)
    if structured:
        print(f"{'Model':<16} | {'Success':<8} | {'1st Valid':<9} | {'Final Valid':<11} | {'Avg Att':<7} | {'Med Lat':<8}")
        print("-" * 70)
        for s in summary_data:
            lat_str = f"{s['median_latency_s']}s" if s['median_latency_s'] else "N/A"
            succ_str = f"{s['successful_trials']}/{s['total_trials']}"
            f_pct = f"{s['first_attempt_valid_pct']}%" if s['first_attempt_valid_pct'] != "N/A" else "N/A"
            fin_pct = f"{s['final_valid_pct']}%" if s['final_valid_pct'] != "N/A" else "N/A"
            att = str(s['avg_attempts_used'])
            print(f"{s['model_name']:<16} | {succ_str:<8} | {f_pct:<9} | {fin_pct:<11} | {att:<7} | {lat_str:<8}")
    else:
        print(f"{'Model':<18} | {'Success':<8} | {'Median Latency':<14} | {'Tok/s':<10} | {'RAM (MB)':<10}")
        print("-" * 70)
        for s in summary_data:
            lat_str = f"{s['median_latency_s']}s" if s['median_latency_s'] else "N/A"
            tps_str = f"{s['avg_tokens_per_second']}" if s['avg_tokens_per_second'] else "N/A"
            ram_str = f"{s['avg_peak_ram_mb']}" if s['avg_peak_ram_mb'] else "N/A"
            succ_str = f"{s['successful_trials']}/{s['total_trials']}"
            print(f"{s['model_name']:<18} | {succ_str:<8} | {lat_str:<14} | {tps_str:<10} | {ram_str:<10}")
    print("-" * 70)
    print(f"Raw run records : {RAW_RESULTS_CSV}")
    print(f"Summary table   : {SUMMARY_RESULTS_CSV}")
    print("Evaluation note : Schema validity is separate from answer quality (see data/EVALUATION_RUBRIC.md).")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline Model Benchmark Runner (compare 3 local Ollama models)."
    )
    parser.add_argument(
        "--models",
        "-m",
        nargs="+",
        default=["llama3.2:3b", "qwen2.5:3b", "mistral:latest"],
        help="Space-separated list of 3 model tags (default: llama3.2:3b qwen2.5:3b mistral:latest)",
    )
    parser.add_argument(
        "--prompts",
        "-p",
        type=Path,
        default=DEFAULT_PROMPTS_FILE,
        help="Path to benchmark prompts JSON file.",
    )
    parser.add_argument(
        "--trials",
        "-t",
        type=int,
        default=1,
        help="Number of repeated trials per prompt (default: 1).",
    )
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="Disable initial cold-start warm-up run.",
    )
    parser.add_argument(
        "--structured",
        "-s",
        action="store_true",
        help="Run benchmark with Pydantic structured output validation and bounded retries.",
    )

    args = parser.parse_args()
    run_benchmark(
        models=args.models,
        prompts_file=args.prompts,
        trials_per_prompt=args.trials,
        include_warmup=not args.no_warmup,
        structured=args.structured,
    )


if __name__ == "__main__":
    main()
