# Testing and Evaluation

[Back to README](./README.md)

> **Status:** every test below is **DESIGNED, NOT EXECUTED**. No application code exists yet, so no test has been run. The "Status" column must only be changed to **Executed** when you have really run the test and recorded the result in the execution log (Section 14). Labels are explained in the [README](./README.md#read-this-first-status-legend).

---

## 1. Designed vs Executed Tests

| Term | Meaning |
|---|---|
| **Designed** | The test is written down (steps and expected outcome). |
| **Executed** | The test was actually run; the date, environment, and actual result are recorded. |
| **Passed / Failed** | Only meaningful for executed tests. |

A designed test is a *plan*, not evidence. In the final report, never count designed tests as passed.

## 2. Testing Approach

- **Automated tests** (`pytest`) for logic that does not need a real model: validation, retry limits, error handling, CSV writing. Use a **fake model function** that returns fixed text.
- **Manual or integration tests** with a real local model: model availability, timeouts, end-to-end flow.
- **Evaluation** (quality scoring) is separate from testing; see Section 10.

```python
# Example of a fake model for automated tests [ILLUSTRATIVE]
def fake_model_always_invalid(prompt: str) -> str:
    return "this is not json"

def fake_model_valid(prompt: str) -> str:
    return '{"topic": "T", "questions": [{"question": "What is T really?", "answer": "A", "difficulty": "easy"}]}'
```

## 3. Functional Testing

| ID | Test | Steps | Expected outcome | Status |
|---|---|---|---|---|
| F-01 | Basic question | Ask "What is a token?" with a valid model | A non-empty answer is displayed | Designed, not executed |
| F-02 | Summarize notes | Provide a short sample note file | A summary shorter than the input is shown | Designed, not executed |
| F-03 | Generate exam questions | Request 3 questions on a sample note | Output passes the Pydantic schema; 3 or fewer questions as limited | Designed, not executed |
| F-04 | Switch model | Run with `--model` set to each of the three tags | Each runs; the displayed model name matches | Designed, not executed |
| F-05 | Exit cleanly | Quit the program | No error, no leftover processes from our app | Designed, not executed |

## 4. Model Availability Checks

| ID | Test | Steps | Expected outcome | Status |
|---|---|---|---|---|
| M-01 | Model present | Check a downloaded tag | Check passes | Designed, not executed |
| M-02 | Model missing | Use a tag that is not downloaded | Clear message suggesting `ollama pull <tag>`; no crash | Designed, not executed |
| M-03 | Ollama not running | Stop the Ollama server, then start the app | Clear "cannot reach Ollama" message; no crash | Designed, not executed |
| M-04 | Misspelled tag | Use `nonexistent:tag` | Same behavior as M-02 | Designed, not executed |

## 5. Input Validation

| ID | Test | Input | Expected outcome | Status |
|---|---|---|---|---|
| I-01 | Empty input | `""` or only spaces | Rejected with a helpful message; no model call | Designed, not executed |
| I-02 | Very long input | Text above the configured limit | Rejected or truncated with a visible warning | Designed, not executed |
| I-03 | Special characters | Quotes, emoji, non-English text | Handled without crashing | Designed, not executed |
| I-04 | Missing notes file | Path that does not exist | Clear "file not found" message | Designed, not executed |
| I-05 | Wrong file type | Binary file instead of text | Rejected or clear error | Designed, not executed |

## 6. Output Validation and Structured-Output Testing

| ID | Test | Model output (fake) | Expected outcome | Status |
|---|---|---|---|---|
| O-01 | Valid JSON and schema | Valid exam set | Accepted on attempt 1 | Designed, not executed |
| O-02 | Invalid JSON syntax | `{"topic": "T",` | Failure type `invalid_json` | Designed, not executed |
| O-03 | Missing field | No `answer` | Failure type `schema_error` | Designed, not executed |
| O-04 | Wrong type or value | `"difficulty": "impossible"` | Failure type `schema_error` | Designed, not executed |
| O-05 | Extra text around JSON | `Here you go: {...}` | Treated as invalid unless a documented cleanup step is implemented | Designed, not executed |
| O-06 | Empty list | `"questions": []` | Failure type `schema_error` | Designed, not executed |
| O-07 | Valid but wrong fact | Schema-valid answer containing a false statement | Passes validation (validation does not check facts); quality evaluation should flag it | Designed, not executed |
| O-08 | Truncated output | JSON cut off mid-way | `invalid_json` | Designed, not executed |

## 7. Retry Testing

| ID | Test | Setup | Expected outcome | Status |
|---|---|---|---|---|
| R-01 | Succeeds first time | Fake returns valid text | `attempts == 1` | Designed, not executed |
| R-02 | Fails then succeeds | Fake returns invalid, then valid | `attempts == 2`; both logged correctly | Designed, not executed |
| R-03 | Always fails | Fake always invalid | Stops after exactly `MAX_ATTEMPTS`; raises or returns a failure report | Designed, not executed |
| R-04 | Loop bound | Count calls to the fake in R-03 | Calls equal `MAX_ATTEMPTS` (never more) | Designed, not executed |
| R-05 | Non-retryable error | Fake raises connection error or "model not found" | No retries at all; clear error reported | Designed, not executed |
| R-06 | Retry statistics | Mixed outcomes | First-attempt rate and retry rate computed correctly | Designed, not executed |
| R-07 | Timeout retry limit | Fake raises a timeout every time | At most one timeout retry; total calls never exceed `MAX_ATTEMPTS` | Designed, not executed |

```python
# Example automated test [ILLUSTRATIVE; depends on code not yet written]
def test_retry_is_bounded():
    calls = {"n": 0}
    def always_bad(prompt):
        calls["n"] += 1
        return "not json"
    try:
        get_structured_answer(always_bad, "prompt")
    except StructuredOutputError:
        pass
    assert calls["n"] == MAX_ATTEMPTS
```

## 8. Error Handling and Timeout Handling

| ID | Test | Setup | Expected outcome | Status |
|---|---|---|---|---|
| E-01 | Connection refused | Ollama stopped | User-friendly error; logged | Designed, not executed |
| E-02 | Timeout | Very small timeout setting, long prompt | Request stops at the timeout; error type `timeout`; program continues | Designed, not executed |
| E-03 | Model crash or out of memory | Model too large for RAM (only if safe to try) | Error reported; no endless wait | Designed, not executed |
| E-04 | Unexpected exception | Fake raises an unusual exception | Logged; program exits or returns to menu cleanly | Designed, not executed |
| E-05 | Interrupt | Press Ctrl+C during generation | Clean exit | Designed, not executed |

## 9. Benchmark Repeatability

| ID | Test | Steps | Expected outcome | Status |
|---|---|---|---|---|
| B-01 | Same-settings repeat | Run the same prompt 5 times per model | Variation recorded; spread reported | Designed, not executed |
| B-02 | Warm-up excluded | Mark warm-up rows | Summary ignores `warmup` rows | Designed, not executed |
| B-03 | Same dataset for all models | Compare dataset hash/IDs per model | Identical prompt IDs and text | Designed, not executed |
| B-04 | Metadata saved | Inspect output | Model tags, versions, settings, hardware recorded | Designed, not executed |
| B-05 | Unit conversion | Feed known nanosecond values to the calculator | Correct seconds and tokens per second (check by hand) | Designed, not executed |
| B-06 | Raw data preserved | Run twice | Second run does not erase the first run's raw rows | Designed, not executed |
| B-07 | Measurement sanity | Compare measured RAM with `ollama ps` and the OS monitor | Numbers are in the same general range | Designed, not executed |

If two benchmark sessions on the same hardware differ greatly, investigate background load, thermal throttling, Ollama version changes, or model-tag changes before drawing conclusions.

## 10. Quality Evaluation (Not the Same as Testing)

Testing asks "does the program behave as designed?" Evaluation asks "how good are the answers?"

| ID | Check | Method | Expected outcome | Status |
|---|---|---|---|---|
| Q-01 | Rubric defined before scoring | Rubric document dated before result files | Rubric exists first | Designed, not executed |
| Q-02 | Blind scoring | Model names hidden in scoring sheet | Scorer cannot tell the model | Designed, not executed |
| Q-03 | Consistency check | Re-score a sample or use a second scorer | Agreement level recorded; low agreement leads to rubric revision | Designed, not executed |
| Q-04 | Hallucination check | Prompts whose answers are not in the provided notes | Faithfulness criterion lowers the score for invented facts | Designed, not executed |
| Q-05 | Answer-length bias | Compare score vs length | Longer answers do not receive higher scores automatically | Designed, not executed |

Details of the rubric: [MODEL_BENCHMARK.md](./MODEL_BENCHMARK.md#7-answer-quality).

## 11. Logging Tests

| ID | Test | Expected outcome | Status |
|---|---|---|---|
| L-01 | Failure logged | Each validation failure creates one log entry with attempt number and failure type | Designed, not executed |
| L-02 | No sensitive text by default | Log lines contain lengths/IDs, not note content | Designed, not executed |
| L-03 | Log rotation or size limit | Logs do not grow without bound | Designed, not executed |
| L-04 | Errors logged | Timeouts and connection errors recorded with timestamps | Designed, not executed |

## 12. Privacy Testing

Full procedure: [PRIVACY_AND_SECURITY.md](./PRIVACY_AND_SECURITY.md).

| ID | Test | Expected outcome | Status |
|---|---|---|---|
| P-01 | Code review for network calls | Only calls go to the local Ollama address | Designed, not executed |
| P-02 | Offline run | After models are downloaded, disable network; the assistant still works | Designed, not executed |
| P-03 | Connection inspection | During use, no connections from our app or Ollama to unexpected external hosts **[VERIFY what Ollama does]** | Designed, not executed |
| P-04 | Binding check | Ollama listens on localhost only | Designed, not executed |
| P-05 | Marker test | Put a unique fake secret phrase in a test note; search logs and results for unexpected copies | Designed, not executed |
| P-06 | Repository check | `.gitignore` excludes notes, logs, results with private data | Designed, not executed |

## 13. Test Report Template

For the final report, summarize honestly:

| Category | Designed | Executed | Passed | Failed | Notes |
|---|---|---|---|---|---|
| Functional | TBD | TBD | TBD | TBD | |
| Model availability | TBD | TBD | TBD | TBD | |
| Input validation | TBD | TBD | TBD | TBD | |
| Output / structured | TBD | TBD | TBD | TBD | |
| Retry | TBD | TBD | TBD | TBD | |
| Error and timeout | TBD | TBD | TBD | TBD | |
| Repeatability | TBD | TBD | TBD | TBD | |
| Quality evaluation | TBD | TBD | TBD | TBD | |
| Logging | TBD | TBD | TBD | TBD | |
| Privacy | TBD | TBD | TBD | TBD | |

## 14. Execution Log (fill in when you run tests)

| Date | Test ID | Environment (OS, Ollama, Python, model tag) | Result | Evidence (file or screenshot) | Notes |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

## 15. Limitations of Testing

- Tests cannot prove the model's answers are true.
- Passing tests on one machine does not guarantee behavior on another.
- LLM outputs vary, so some tests must check *properties* (valid, bounded) rather than exact text.
- Privacy tests reduce risk but cannot prove the absence of every leak.
