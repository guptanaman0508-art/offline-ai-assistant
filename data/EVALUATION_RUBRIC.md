# Model Benchmark Answer Quality Evaluation Rubric

> As defined in [MODEL_BENCHMARK.md](../MODEL_BENCHMARK.md#7-answer-quality), answer quality cannot be measured solely by latency or token counts. This rubric establishes transparent, human-verifiable criteria for scoring responses.

## Scoring Criteria (0 to 2 Scale)

Each model response is evaluated against the 5 criteria below:

| Criterion | Score 0 (Poor) | Score 1 (Acceptable) | Score 2 (Good) |
|---|---|---|---|
| **1. Correctness** | Factual errors, inaccurate concepts | Minor imprecision, core fact right | Completely accurate facts |
| **2. Completeness** | Misses most reference points | Mentions some reference points | Covers all reference key points |
| **3. Clarity** | Confusing, disjointed structure | Understandable, slightly verbose | Clear, concise, well-structured |
| **4. Faithfulness** | Severe hallucination / invented facts | Minor unsubstantiated detail | Grounded, zero hallucination |
| **5. Instruction Following** | Ignores requested format/length | Mostly follows format | Perfectly follows requested format |

### Total Score Calculation
- Maximum score per prompt = 10 (5 criteria × 2 points).
- To preserve benchmark integrity, **never invent benchmark scores**.
- The benchmark runner records `quality_score` as empty (`None`) during automated runs until scored manually or verified against key points.
