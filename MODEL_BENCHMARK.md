# Model Benchmark Methodology

[Back to README](./README.md)

> **Status:** methodology only. **No measurements have been taken.** Every table value is `TBD`. Labels are explained in the [README](./README.md#read-this-first-status-legend).

---

## 1. What Is Benchmarking?

**Benchmarking** means measuring things in a controlled, repeatable way so that different options can be compared fairly. Here, we compare three local LLMs on the same computer, with the same tasks.

## 2. Why Compare Models?

- Models trade off quality, speed, and memory.
- Marketing claims and online leaderboards do not tell you how a model behaves **on your hardware with your tasks**.
- Comparison produces evidence for choosing the model used in the semester-notes assistant.
- Results can reveal surprises (for example, a smaller model that follows JSON formats more reliably).

## 3. Hardware Record (fill in before testing)

| Item | Value |
|---|---|
| Operating system and version | TBD |
| CPU model and core count | TBD |
| Total system RAM | TBD |
| GPU model (if any) | TBD |
| GPU memory (VRAM) (if any) | TBD |
| Free disk space | TBD |
| Ollama version | TBD |
| Python version | TBD |
| `ollama` library / Pydantic / psutil versions | TBD |
| Power mode (laptop: plugged in?) | TBD |
| Date of benchmark | TBD |

## 4. How to Select Three Models

Do **not** choose the models until you know your hardware. Follow this process:

1. **Check hardware.** Note RAM and GPU memory (table above).
2. **Set a memory budget.** Leave room for the operating system and other programs. As a rough planning idea, the model plus its working memory should fit comfortably inside free RAM/VRAM. **[VERIFY with your own measurements; this is only a planning guide.]**
3. **Browse the Ollama library** (<https://ollama.com/library>) for models with sizes that fit the budget.
4. **Check compatibility.** Confirm the model runs in Ollama and supports the features you need (for example, structured output, long context) **[VERIFY per model]**.
5. **Read each license.** Open-weight licenses differ. Some are permissive; some restrict commercial use or require you to follow usage policies. Never assume two models have the same terms.
6. **Prefer variety, but keep it fair.** For example, choose models in a similar size class from different families, or choose one family at three sizes. State which comparison you are making; they answer different questions.
7. **Record exact tags.** `model-name:tag` must be written down (for example the tag shows size and quantization). "latest" can change over time.
8. **Document the reason** for each choice in a short table.

| Slot | Model name | Exact tag | Reason chosen | License (link) |
|---|---|---|---|---|
| Model A | TBD | TBD | TBD | TBD |
| Model B | TBD | TBD | TBD | TBD |
| Model C | TBD | TBD | TBD | TBD |

### Open-source software vs open-weight models

- **Ollama** and many Python libraries are **open-source software**: their *code* is available under a software license.
- **Open-weight models** release the trained *weights* (the model file), but that does not always mean they are "open source" in the strict sense: training data, training code, and unrestricted rights may not be provided. Each model has its own license. Read it.

## 5. Model Size vs RAM Usage

| Concept | Meaning |
|---|---|
| **Model size (download/disk size)** | How big the model file is on disk. Shown by `ollama list`. |
| **Runtime memory (RAM or VRAM usage)** | How much memory is used while the model is loaded and generating. |

They are **not the same**. Runtime memory depends on:

- the model (number of parameters and architecture),
- **quantization** (storing weights with fewer bits, which shrinks the model; more compression can reduce quality),
- **context length** (longer context needs more memory for the attention cache, often called the KV cache),
- the workload (prompt length, number of parallel requests),
- the runtime (Ollama version, CPU vs GPU, memory-mapping behavior).

A model whose file is 4 GB may use noticeably more than 4 GB while running. Measure it; do not guess.

### How to measure RAM **[PLANNED]**

| Method | What it shows | Notes |
|---|---|---|
| `ollama ps` | Size of loaded models and whether they sit on CPU/GPU | Quick manual check **[VERIFY output columns]** |
| `psutil` | Memory used by the Ollama process(es) | Process names differ by OS and version; identify them first (Task Manager / Activity Monitor / `ps`) **[VERIFY]** |
| System memory before vs after loading | Total extra memory in use | Close other programs first |
| GPU tools (for example `nvidia-smi` on NVIDIA systems) | VRAM use | Only if you have a supported GPU |

Always measure the **Ollama server process**, not your Python script (the model lives in Ollama, not in Python). Record **baseline** (model not loaded) and **peak** (during generation). On computers with unified memory (some laptops), CPU and GPU share RAM, which makes separate numbers harder to interpret.

## 6. Latency Metrics Explained

**Latency** is waiting time. Several different times matter:

| Metric | Definition | How to measure |
|---|---|---|
| **Time to first token (TTFT)** | Time from sending the request until the first piece of output arrives | Use *streaming*; start a timer before the request; stop at the first non-empty chunk |
| **Total response time** (total generation time) | Time from sending the request until the last token arrives | Timer around the full request |
| **Model load time** | Time to load weights into memory | `load_duration` in the response **[VERIFY]**; large on the first (cold) request |
| **Prompt processing time** | Time to read the input prompt | `prompt_eval_duration` **[VERIFY]** |
| **Generation time** | Time spent producing output tokens | `eval_duration` **[VERIFY]** |
| **Tokens per second** | Speed of generation | `eval_count / (eval_duration in seconds)` |

Do not mix these up:

- TTFT answers "how long until it starts responding?" (feels like responsiveness).
- Total time answers "how long until it finishes?" (depends on answer length).
- A model can have a quick TTFT but a slow generation speed, or the reverse.
- Tokens per second is only meaningful if you also record how many tokens were produced (answer length differs between models).

> Ollama returns durations in **nanoseconds** **[VERIFY]**. Convert: seconds = nanoseconds / 1,000,000,000.

## 7. Answer Quality

"Quality" cannot be measured by a stopwatch. You need a **defined evaluation method** written *before* running the tests.

### Suggested method **[PLANNED]**

1. **Fixed dataset.** 20 to 40 prompts (exact number TBD) in categories matching the real use: factual Q&A from provided notes, explanation, summarization, exam-question generation.
2. **Reference material.** For each prompt, store the source notes and a short "key points that must appear" list.
3. **Rubric.** Score each answer on a small scale, for example 0 to 2 per criterion:

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Correctness (agrees with the notes/reference) | Wrong | Partly right | Right |
| Completeness (covers key points) | Misses most | Misses some | Covers all |
| Clarity | Confusing | Understandable | Clear |
| Faithfulness (no invented facts beyond the notes) | Invents facts | Minor invention | None |
| Follows instructions (length, format) | Ignores | Partly | Fully |

4. **Blind scoring.** Hide model names when scoring so you do not favor a model.
5. **Consistency check.** Re-score a sample later, or ask a classmate to score the same sample, then compare. Large disagreement means the rubric is unclear.
6. **Optional automatic aids.** Simple checks such as "does the answer contain each key term?" are cheap but crude. Using one LLM to grade another ("LLM-as-judge") is possible but can be biased; if used, say so and spot-check it by hand **[VERIFY suitability]**.

Report the method together with the scores.

## 8. Structured-Output Metrics

For tasks that require JSON (for example exam-question generation):

| Metric | Formula |
|---|---|
| **First-attempt valid rate** | runs valid on attempt 1 ÷ total structured runs |
| **Eventual valid rate (structured-output success rate)** | runs valid within `MAX_ATTEMPTS` ÷ total structured runs |
| **Retry rate** | runs needing more than one attempt ÷ total structured runs |
| **Average attempts** | total attempts ÷ total structured runs |
| **Error rate** | runs ending in failure (timeout, connection error, or still invalid after the last attempt) ÷ total runs |

Valid means "passes the Pydantic schema". It does **not** mean correct. See [PYDANTIC_AND_VALIDATION.md](./PYDANTIC_AND_VALIDATION.md).

## 9. Repeated Trials

LLM output varies, and so does timing (background tasks, thermal throttling, caching). One run proves little.

- Repeat each prompt **N times** per model (suggested starting point: 5; adjust after you see the variation).
- Report the **median** (less affected by outliers), plus **minimum, maximum, and standard deviation or interquartile range**.
- If a result changes a lot between runs, say so; do not hide it behind an average.
- Setting a fixed random seed and temperature reduces output variation but may not remove it completely **[VERIFY determinism on your setup]**. Decide whether to benchmark at temperature 0 (more repeatable) or at your intended real-use setting, and state the choice.

## 10. Warm-Up Runs

The first request to a model usually includes loading it from disk into memory (a **cold start**). Later requests reuse the loaded model (a **warm** state).

- Run one or more warm-up requests per model first and **discard** them.
- Record cold-start load time **separately** if you care about it (it matters for how the assistant feels at startup).
- Check with `ollama ps` that the model stays loaded between runs, or set a keep-alive option **[VERIFY]**.

## 11. Fair Comparison Rules

1. Same machine, same OS, same Ollama version for all models.
2. Same prompts, same dataset, same order (or randomized identically/with recorded seed).
3. Same generation settings (temperature, seed, maximum output tokens, context length) unless a model *requires* a different value; if so, document it.
4. Only one model loaded at a time; unload or wait before switching so memory is not shared.
5. Close heavy programs; keep the laptop plugged in; avoid running other benchmarks at the same time.
6. Same number of warm-up and measured runs per model.
7. Same retry limit and the same validation schema for every model.
8. Same rubric and blind scoring.
9. Record exact model tags, versions, and all settings.
10. Do not tune prompts for one model only. If prompt tuning is allowed, give every model equal effort.
11. Report failures instead of deleting them.

## 12. Comparison Table (blank, no measurements)

| Metric | Model A | Model B | Model C |
|---|---|---|---|
| Model name | TBD | TBD | TBD |
| Model version/tag | TBD | TBD | TBD |
| Model size | TBD | TBD | TBD |
| RAM usage | TBD | TBD | TBD |
| Time to first token | TBD | TBD | TBD |
| Total response time | TBD | TBD | TBD |
| Tokens per second | TBD | TBD | TBD |
| Answer quality | TBD | TBD | TBD |
| Valid structured outputs (first attempt / after retries) | TBD / TBD | TBD / TBD | TBD / TBD |
| Retry rate | TBD | TBD | TBD |

> **How to read the "Valid structured outputs" row:** report two numbers per model, separated by a slash. The first is the **first-attempt valid rate** (valid on attempt 1). The second is the **eventual valid rate** (valid within `MAX_ATTEMPTS`). Reporting only the second would let retries hide a model that often fails the first time. The "Retry rate" row is the share of runs that needed more than one attempt.

## 13. How to Collect Real Measurements **[PLANNED]**

1. Complete the hardware record (Section 3).
2. Choose and document three models (Section 4).
3. Create the fixed dataset and rubric **before** running anything.
4. Write the measurement code (timing with a high-resolution timer such as `time.perf_counter()`, token counts from Ollama's response, memory with `psutil`).
5. Test the measurement code on one prompt and compare its output with `ollama ps` and Task Manager / Activity Monitor to check that numbers are plausible.
6. Run warm-up, then measured runs for each model.
7. Save every run to `raw_runs.csv`.
8. Score quality (blind).
9. Aggregate to `summary.csv` and render the table.

### Suggested raw CSV columns **[PLANNED]**

```csv
run_id,timestamp,model_tag,prompt_id,category,run_type,attempt_count,ttft_s,total_s,load_s,prompt_tokens,eval_tokens,tokens_per_s,baseline_ram_mb,peak_ram_mb,valid_first_try,valid_final,error_type,quality_score
```

`run_type` is `warmup` or `measured`. Warm-up rows can be stored but must be excluded from the summary.

## 14. How to Interpret Results

- **No single winner.** Decide which metrics matter most for your use case, then weigh them. For example, a student notes assistant might value quality and structured-output reliability over raw speed.
- **Look at spread, not just the middle.** A model with a good median but frequent failures is risky.
- **Check answer length.** A model that writes shorter answers finishes sooner; compare tokens per second *and* total time.
- **Compare cost to benefit.** If Model B uses twice the RAM for a small quality gain, is that worth it?
- **Hardware limits count.** If a model forces swapping to disk, its speed numbers will be poor, and that is a valid finding for your machine.
- **Small differences may be noise.** If medians are close and spreads overlap, call it a tie.
- **State the conclusion narrowly:** "On this hardware, with this dataset and these settings, Model X performed best at Y."

### Optional weighted decision matrix **[ILLUSTRATIVE: weights are examples, not recommendations]**

| Criterion | Weight (example) | Model A score | Model B score | Model C score |
|---|---|---|---|---|
| Answer quality | TBD | TBD | TBD | TBD |
| Structured-output reliability | TBD | TBD | TBD | TBD |
| Speed (TTFT, tokens/s) | TBD | TBD | TBD | TBD |
| Memory use | TBD | TBD | TBD | TBD |
| License fit | TBD | TBD | TBD | TBD |

## 15. Benchmark Limitations

- Results are valid only for the tested hardware, software versions, models, prompts, and settings.
- Three models do not represent "local LLMs" in general.
- A small dataset can give misleading quality scores; human scoring is subjective.
- Memory measurements are approximate and depend on the operating system's accounting.
- Background activity and thermal throttling add noise.
- Models and Ollama change over time; tags such as `latest` may point to different files later.
- Speed on one machine does not predict speed on another.
- Benchmark prompts may not match real notes; the final assistant should be spot-checked on real use.
- Quality depends on the prompt wording; a different prompt could change the ranking.
