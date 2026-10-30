# Offline AI Assistant - Three-Model Benchmark Report

> **Document Status:** Empirical benchmark report based on verified local run results recorded in `results/raw_runs.csv` and `results/summary.csv`.

---

## 1. Test Environment and Model Details

All metrics were captured locally on physical hardware through the project's automated benchmark harness (`src/benchmark.py` and `src/metrics.py`) communicating with the local Ollama daemon.

| Environment Property | Specification |
|---|---|
| **Host Operating System** | macOS (Darwin 25.6.0, Apple Silicon `arm64`) |
| **Hardware Platform** | MacBook Air (Apple M4, 10 CPU cores: 10 physical, 10 logical) |
| **System Memory** | 16.0 GB Unified RAM |
| **Local Inference Server** | Ollama (`http://localhost:11434`) |
| **Target Models Evaluated** | `llama3.2:3b`, `qwen2.5:3b`, `mistral:latest` |
| **Benchmark Dataset** | Fixed 5-prompt academic suite (`data/benchmark_prompts.json`) |
| **Execution Date** | 2026-10-25 |

### Evaluated Models

1. **`llama3.2:3b`**: Meta Llama 3.2 lightweight open-weight model (~3B parameters).
2. **`qwen2.5:3b`**: Alibaba Cloud Qwen 2.5 open-weight model (~3B parameters).
3. **`mistral:latest`**: Mistral AI open-weight model (~7B parameters).

---

## 2. Three-Model Benchmark Summary Comparison

The table below presents the verified aggregate measurements extracted directly from `results/summary.csv`.

| Model Name | Successful Prompts | Success Rate | Median Latency | Min Latency | Max Latency | Tokens / Sec | Cold-Start Load Time | Avg Reported Ollama RAM (MB) | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **`llama3.2:3b`** | **5 / 5** | 100.0% | **5.168 s** | 2.128 s | 6.263 s | 43.35 tok/s | 1.598 s | **2643.08 MB** | OK |
| **`qwen2.5:3b`** | **5 / 5** | 100.0% | 6.362 s | 1.716 s | 7.881 s | **47.23 tok/s** | 1.547 s | 4563.11 MB | OK |
| **`mistral:latest`** | **5 / 5** | 100.0% | 17.787 s | 10.460 s | 35.885 s | 13.11 tok/s | 2.865 s | 4540.91 MB | OK |

> **Source Verification Note:** All reported terminal summary numbers match `results/summary.csv` exactly. The earlier single-model run (5.08 s median latency, 2036.68 MB RAM) represents an initial individual run preserved in `results/raw_runs.csv`, whereas the values above reflect the complete three-model execution pass recorded in `results/summary.csv`.

---

## 3. Key Findings & Performance Interpretation

1. **100% Request Completion Across All Models**:
   - All three models completed all 5 prompts successfully (`5/5`, 100.0% success rate) without server disconnects, request timeouts, or unhandled exceptions.
2. **Lowest Latency & Lowest Reported RAM Footprint**:
   - **`llama3.2:3b`** demonstrated the lowest median latency (**5.168 seconds**) and the lowest average reported process RAM footprint (**2643.08 MB**). For interactive command-line use on an entry-level Apple Silicon laptop, it yielded the fastest overall turnaround time.
3. **Highest Raw Generation Throughput**:
   - **`qwen2.5:3b`** achieved the highest token generation throughput (**47.23 tokens/second**), outperforming `llama3.2:3b` (43.35 tokens/second) in active decoding speed. However, because Qwen generated longer, more comprehensive answers for several prompts (e.g., 382 tokens on `q3_acid_properties` vs. 198 tokens for Llama), its median total turnaround latency was slightly higher (6.362 s).
4. **Parameter Size Impact (3B vs. 7B)**:
   - **`mistral:latest`** (~7B parameters) required significantly longer generation times (median latency: **17.787 seconds**, with prompt `q4` reaching 35.885 s) and lower decoding speed (**13.11 tokens/second**). This illustrates the direct trade-off between model parameter capacity and computational turnaround when running locally on laptop hardware without dedicated high-bandwidth discrete GPU memory.

---

## 4. Individual Prompt Breakdown (Current Three-Model Run)

The detailed measurements per prompt below are taken directly from the measured trials in `results/raw_runs.csv`:

### A. `llama3.2:3b`
| Prompt ID | Category | Status | Latency | Tokens | Eval Duration | Token Speed | Peak RAM |
|---|---|---|---|---|---|---|---|
| *q1_binary_search (Warm-up)* | `factual_explanation` | `SUCCESS` | 7.748 s | 276 | 6.006 s | 45.96 tok/s | 2960.53 MB |
| **q1_binary_search** | `factual_explanation` | `SUCCESS` | 5.168 s | 212 | 5.129 s | 41.33 tok/s | 2588.97 MB |
| **q2_process_vs_thread** | `factual_explanation` | `SUCCESS` | 2.128 s | 88 | 2.043 s | 43.07 tok/s | 2620.72 MB |
| **q3_acid_properties** | `summarization` | `SUCCESS` | 4.963 s | 198 | 4.875 s | 40.62 tok/s | 2638.17 MB |
| **q4_rest_principles** | `factual_explanation` | `SUCCESS` | 5.457 s | 244 | 5.366 s | 45.47 tok/s | 2667.19 MB |
| **q5_generate_exam_question** | `exam_generation` | `SUCCESS` | 6.263 s | 282 | 6.099 s | 46.24 tok/s | 2700.33 MB |

### B. `qwen2.5:3b`
| Prompt ID | Category | Status | Latency | Tokens | Eval Duration | Token Speed | Peak RAM |
|---|---|---|---|---|---|---|---|
| *q1_binary_search (Warm-up)* | `factual_explanation` | `SUCCESS` | 6.344 s | 218 | 4.611 s | 47.28 tok/s | 4687.16 MB |
| **q1_binary_search** | `factual_explanation` | `SUCCESS` | 3.231 s | 152 | 3.200 s | 47.50 tok/s | 4552.81 MB |
| **q2_process_vs_thread** | `factual_explanation` | `SUCCESS` | 1.716 s | 78 | 1.629 s | 47.88 tok/s | 4562.19 MB |
| **q3_acid_properties** | `summarization` | `SUCCESS` | 7.881 s | 369 | 7.795 s | 47.34 tok/s | 4568.80 MB |
| **q4_rest_principles** | `factual_explanation` | `SUCCESS` | 7.751 s | 359 | 7.660 s | 46.87 tok/s | 4586.09 MB |
| **q5_generate_exam_question** | `exam_generation` | `SUCCESS` | 6.362 s | 289 | 6.206 s | 46.56 tok/s | 4545.67 MB |

### C. `mistral:latest`
| Prompt ID | Category | Status | Latency | Tokens | Eval Duration | Token Speed | Peak RAM |
|---|---|---|---|---|---|---|---|
| *q1_binary_search (Warm-up)* | `factual_explanation` | `SUCCESS` | 18.169 s | 331 | 15.109 s | 21.91 tok/s | 4527.03 MB |
| **q1_binary_search** | `factual_explanation` | `SUCCESS` | 16.806 s | 264 | 16.727 s | 15.78 tok/s | 4513.77 MB |
| **q2_process_vs_thread** | `factual_explanation` | `SUCCESS` | 10.460 s | 158 | 10.146 s | 15.57 tok/s | 4556.64 MB |
| **q3_acid_properties** | `summarization` | `SUCCESS` | 19.056 s | 251 | 18.686 s | 13.43 tok/s | 4567.61 MB |
| **q4_rest_principles** | `factual_explanation` | `SUCCESS` | 35.885 s | 383 | 35.610 s | 10.76 tok/s | 4536.80 MB |
| **q5_generate_exam_question** | `exam_generation` | `SUCCESS` | 17.787 s | 168 | 16.799 s | 10.00 tok/s | 4529.72 MB |

---

## 5. Explanation of Benchmark Metrics

1. **Cold-Start Load Time (`cold_start_load_s`)**:
   - The time reported by Ollama spent reading model weights from storage into memory during the initial cold request.
2. **Median Latency (`median_latency_s`)**:
   - The middle response latency value among measured runs. Median is prioritized over arithmetic mean to prevent skew from single outlier prompts.
3. **Token Generation Speed (`tokens_per_second`)**:
   - Calculated as `eval_count / eval_duration_s` using native duration counters reported directly by Ollama. It reflects active token decoding throughput.
4. **Reported Ollama RAM (`avg_peak_ram_mb`)**:
   - Measured Resident Set Size (RSS) memory of the background Ollama server process (`ollama serve`) collected via `psutil`. **Important:** This reflects the process memory allocated to the Ollama daemon as reported by the project's metric collector, **not** total system-wide memory consumption or entire unified OS cache.
5. **Success Rate (`success_rate_pct`)**:
   - Percentage of prompts evaluated without connection loss, timeouts, or runtime exceptions.

---

## 6. Answer Quality Evaluation

> **Methodology:** Responses to all five prompts were generated using `scripts/export_eval_responses.py` (with deterministic temperature 0.0) and saved to `results/full_responses_for_eval.json`. Each response was manually scored against [data/EVALUATION_RUBRIC.md](../data/EVALUATION_RUBRIC.md) across five criteria (0–2 scale, maximum score 10: *Correctness*, *Completeness*, *Clarity*, *Faithfulness*, *Instruction Following*). The individual ratings and notes are recorded in `human_eval_scores_reviewed.csv`.

### Average Quality Scores

| Model Name | Evaluated Prompts | Mean Score (out of 10) | Average Score (%) | Key Quality Strengths & Observations |
|---|:---:|:---:|:---:|---|
| **`llama3.2:3b`** | 5 | **9.0 / 10** | **90.0%** | **Highest overall score.** Consistent instruction adherence, excellent clarity on ACID properties and REST principles (both scored 10/10), and faithful explanations. Minor point deducted for slightly dense nested formatting on binary search and omitting context-switching speed on threads. |
| **`qwen2.5:3b`** | 5 | **8.6 / 10** | **86.0%** | **Strong structure and exam question generation.** Scored a perfect 10/10 on the multiple-choice exam question generation (`q5`). Deductions occurred due to claiming best-case binary search is $O(\log n)$ instead of $O(1)$ and repeating statelessness rather than cleanly separating client-server architecture in `q4`. |
| **`mistral:latest`** | 5 | **8.4 / 10** | **84.0%** | **Comprehensive depth on database & data structures.** Perfect 10/10 on ACID properties (`q3`) and exam question generation (`q5`). However, it struggled with strict length and constraint adherence: added unrequested filler on `q1`, used four sentences instead of three on `q2`, and scored 5/10 on `q4` by conflating REST principles and generating excessive, unstructured text. |

### Prompt-by-Prompt Quality Score Breakdown

| Prompt ID | `llama3.2:3b` | `qwen2.5:3b` | `mistral:latest` | Prompt Objective / Topic |
|---|:---:|:---:|:---:|---|
| **q1_binary_search** | 8 / 10 | 8 / 10 | 9 / 10 | 3 clear bullet points + time complexity |
| **q2_process_vs_thread** | 9 / 10 | 9 / 10 | 8 / 10 | 3-sentence contrast between process and thread |
| **q3_acid_properties** | 10 / 10 | 9 / 10 | 10 / 10 | Summary of relational database ACID properties |
| **q4_rest_principles** | 10 / 10 | 7 / 10 | 5 / 10 | 3 core architectural REST principles |
| **q5_generate_exam_question** | 8 / 10 | 10 / 10 | 10 / 10 | MCQ on stack vs queue with 4 options and answer |
| **Average Score** | **9.0 / 10** | **8.6 / 10** | **8.4 / 10** | |

---

## 7. Critical Limitations & Distinctions

- **Separate Evaluation Runs**:
  - The answer-quality scores above represent rubric-based assessments of **five newly generated evaluation responses** captured in `results/full_responses_for_eval.json` using deterministic generation (temperature 0.0). They are **not** the exact original responses captured during the speed-benchmark runs, although both utilized identical prompt texts from `data/benchmark_prompts.json`.
- **Preliminary Nature of the Evaluation**:
  - This evaluation is preliminary because only five prompts were scored per model. While sufficient for academic demonstration and illustrating the evaluation methodology, a broader prompt suite (20–50 prompts) is recommended for statistically robust generalization.
- **Performance vs. Quality Trade-Off**:
  - Faster generation speed (`tokens_per_second`) does not dictate higher answer quality. For instance, `qwen2.5:3b` generated tokens faster than `llama3.2:3b` (47.23 tok/s vs. 43.35 tok/s), but `llama3.2:3b` scored higher in instruction-following precision and conceptual completeness on REST principles.
- **Reported Process RAM vs. Total System RAM**:
  - The RAM metric measures the Resident Set Size (RSS) of the background `ollama serve` process via `psutil`, **not** total system-wide memory or the unified memory cache of macOS.

