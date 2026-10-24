# Offline AI Assistant - Model Benchmark Report

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
| **Target Model Evaluated** | `llama3.2:3b` |
| **Model Size / Family** | Meta Llama 3.2 lightweight open-weight model (3 Billion parameters) |
| **Benchmark Dataset** | Fixed 5-prompt academic suite (`data/benchmark_prompts.json`) |
| **Execution Date** | 2026-10-25 |

---

## 2. Benchmark Summary Results

The table below presents the verified aggregate measurements from `results/summary.csv` for `llama3.2:3b`.

| Metric | Measured Value | Notes |
|---|---|---|
| **Model Name** | `llama3.2:3b` | Tag tested via local Ollama daemon |
| **Successful Prompts** | **5 / 5** (100.0%) | Zero connection errors, timeouts, or unhandled exceptions |
| **Warm-up Duration** | **4.912 s** | Initial cold-start request (load + first prompt) isolated from summary |
| **Median Latency** | **5.08 s** | Median turnaround time across measured prompts |
| **Min Latency** | **1.885 s** | Prompt `q2_process_vs_thread` (84 tokens generated) |
| **Max Latency** | **5.625 s** | Prompt `q1_binary_search` (254 tokens generated) |
| **Generation Speed** | **45.68 tokens/s** | Average generation throughput (`eval_count / eval_duration`) |
| **Peak Ollama Memory (RAM)** | **2036.68 MB** | Average resident set size (RSS) of Ollama daemon during inference |
| **Status Notes** | **OK** | All 5 prompts executed successfully |

---

## 3. Individual Prompt Breakdown

The following data is extracted directly from the measured trials in `results/raw_runs.csv`:

| Prompt ID | Category | Status | Latency | Tokens | Eval Duration | Token Speed | Peak RAM |
|---|---|---|---|---|---|---|---|
| *q1_binary_search (Warm-up)* | `factual_explanation` | `SUCCESS` | 4.912 s | 218 | 4.789 s | 45.52 tok/s | 1983.86 MB |
| **q1_binary_search** | `factual_explanation` | `SUCCESS` | 5.625 s | 254 | 5.591 s | 45.43 tok/s | 2014.03 MB |
| **q2_process_vs_thread** | `factual_explanation` | `SUCCESS` | 1.885 s | 84 | 1.800 s | 46.68 tok/s | 2047.56 MB |
| **q3_acid_properties** | `summarization` | `SUCCESS` | 4.244 s | 191 | 4.161 s | 45.90 tok/s | 2063.22 MB |
| **q4_rest_principles** | `factual_explanation` | `SUCCESS` | 5.423 s | 244 | 5.333 s | 45.75 tok/s | 2089.73 MB |
| **q5_generate_exam_question** | `exam_generation` | `SUCCESS` | 5.080 s | 220 | 4.931 s | 44.62 tok/s | 1968.84 MB |

---

## 4. Explanation of Benchmark Metrics

1. **Warm-up Duration (`cold_warmup`)**:
   - The wall-clock time required for the initial request. This measures the cost of loading model weights from SSD storage into active unified RAM and initializing the attention Key-Value (KV) cache. It is isolated from subsequent trials so it does not distort ongoing response times.
2. **Median Latency (`median_latency_s`)**:
   - The middle response latency value when sorting the measured runs. The median is reported rather than a simple average because it is robust against transient system spikes (such as background OS disk or CPU activity).
3. **Token Generation Speed (`tokens_per_second`)**:
   - Calculated as `eval_count / eval_duration_s` using native duration counters reported directly by the Ollama inference engine. This represents the raw decoding throughput independent of network transfer overhead.
4. **Ollama Process RAM (`peak_ram_mb`)**:
   - Sampled Resident Set Size (RSS) memory of the background Ollama server process (`ollama serve`) measured via `psutil`. This reflects the real physical memory footprint needed to host the 3B parameter model in RAM.
5. **Success Rate (`success_rate_pct`)**:
   - Percentage of prompt requests that completed without timeouts, network disconnections, or model crashes.

---

## 5. Limitations of Current Results

- **Single Model Tested**:
  - Only `llama3.2:3b` has been evaluated so far. Comparative conclusions about speed, memory efficiency, or accuracy relative to other architectures cannot be drawn until additional models are benchmarked.
- **Unscored Qualitative Accuracy**:
  - The benchmark suite measures response latency, memory, and generation throughput, but **answer quality has not yet been independently scored**. Fast responses do not guarantee factual accuracy or absence of hallucinations. Responses must be scored against [data/EVALUATION_RUBRIC.md](../data/EVALUATION_RUBRIC.md).
- **Dataset Size**:
  - The test suite used 5 fixed prompts. While suitable for smoke testing and baseline validation, a larger and more varied dataset will provide higher statistical confidence.
- **Single Run Trial**:
  - Results reflect a single pass per prompt (`trials=1`). Repeated runs (`--trials 3` or `--trials 5`) are planned to evaluate run-to-run variance and thermal stability.

---

## 6. Planned Three-Model Comparison

To complete the project benchmark objective, two additional models will be pulled and benchmarked under the exact same conditions:

| Comparison Slot | Model Name & Tag | Architecture / Family | Parameter Size | Benchmark Status |
|---|---|---|---|---|
| **Model 1** | `llama3.2:3b` | LLaMA 3.2 (Meta) | 3B | **Completed** |
| **Model 2** | `qwen2.5:3b` | Qwen 2.5 (Alibaba Cloud) | 3B | Planned (`ollama pull qwen2.5:3b`) |
| **Model 3** | `mistral:latest` (or `phi3:mini`) | Mistral / Phi | ~3.8B - 7B | Planned (`ollama pull mistral`) |

Once all three models are executed, the updated `results/summary.csv` will provide a side-by-side comparative table evaluating:
- Throughput trade-offs across model families.
- RAM utilization differences on Apple Silicon unified memory.
- Bounded-retry structured output reliability (`--structured`).
