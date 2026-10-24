# Pydantic and Validation

[Back to README](./README.md)

> **Status:** explanatory examples only. The code below is a short teaching illustration. It has **not** been run as part of this project. Labels are explained in the [README](./README.md#read-this-first-status-legend). Examples assume **Pydantic v2** and Python 3.10+ **[VERIFY against your installed versions]**.

---

## 1. What Is Structured Data?

**Structured data** is information organized in a predictable shape, so a program can read it reliably. A table, a spreadsheet row, or a JSON object are structured. A free-form paragraph is *unstructured*.

Why we need it: the assistant should show exam questions as a neat list. To do that, the program must know where each question, answer, and difficulty is. Parsing loose prose is fragile.

## 2. What Is JSON?

**JSON** (JavaScript Object Notation) is a text format for structured data. It uses:

- objects: `{ "key": value }`
- lists: `[ ... ]`
- strings in double quotes, numbers, `true`/`false`, `null`

```json
{
  "topic": "Photosynthesis",
  "questions": [
    {"question": "What is produced besides sugar?", "answer": "Oxygen", "difficulty": "easy"}
  ]
}
```

Common mistakes models make: single quotes instead of double quotes, trailing commas, comments, extra text before or after the JSON, and unfinished output if the token limit is reached.

## 3. What Is a Schema?

A **schema** is a description of what valid data must look like: which fields exist, their types, and rules (for example "difficulty must be easy, medium, or hard"). It is a contract between your program and the model.

## 4. What Does Pydantic Do?

**Pydantic** is a Python library that:

1. lets you describe a schema as a Python class,
2. checks data against it,
3. converts valid data into a typed Python object,
4. raises a clear `ValidationError` listing what is wrong.

## 5. Why LLMs May Return Invalid Outputs

LLMs generate text by predicting likely next tokens. They are not guaranteed to follow a format. Typical reasons:

- the prompt's format instructions were ignored or misunderstood,
- the model adds explanations around the JSON,
- the output is cut off (token limit reached),
- the model invents field names or uses the wrong type,
- smaller models and long prompts increase the risk,
- randomness (temperature) changes behavior between runs.

Some Ollama versions can constrain output to a JSON schema through a `format` option, which greatly improves, but may not perfectly guarantee, validity in every case **[VERIFY in the current Ollama docs and per model]**. Always validate anyway.

## 6. How to Define a Pydantic Model **[ILLUSTRATIVE]**

```python
from typing import Literal
from pydantic import BaseModel, Field


class ExamQuestion(BaseModel):
    question: str = Field(min_length=10)
    answer: str = Field(min_length=1)
    difficulty: Literal["easy", "medium", "hard"]


class ExamQuestionSet(BaseModel):
    topic: str = Field(min_length=1)
    questions: list[ExamQuestion] = Field(min_length=1, max_length=10)
```

Explanation:

- `BaseModel` marks the class as a Pydantic schema.
- `str`, `list[...]` are type requirements.
- `Field(min_length=...)` adds length rules (for lists, it limits the number of items).
- `Literal[...]` allows only the listed values.

## 7. How to Validate an LLM Response **[ILLUSTRATIVE]**

```python
from pydantic import ValidationError

raw_text = '{"topic": "Photosynthesis", "questions": []}'   # imagine this came from the model

try:
    result = ExamQuestionSet.model_validate_json(raw_text)
    print("Valid:", result.topic)
except ValidationError as error:
    print("Invalid output")
    print(error)            # shows which field failed and why
```

`model_validate_json` does two jobs: it parses the JSON text, then checks the schema. Here the example fails because `questions` is empty (minimum is 1).

To ask Ollama for schema-shaped output **[VERIFY syntax for your library version]**:

```python
import ollama

response = ollama.chat(
    model="<model-tag>",
    messages=[{"role": "user", "content": "Create 3 exam questions about photosynthesis."}],
    format=ExamQuestionSet.model_json_schema(),   # gives the model the schema
    options={"temperature": 0},
)
raw_text = response["message"]["content"]
```

## 8. How to Handle Validation Errors

Distinguish the failure type, because each is counted differently:

| Failure type | Example | Pydantic detail |
|---|---|---|
| Invalid JSON (syntax) | Missing quote, extra text | `ValidationError` of type `json_invalid` |
| Missing field | No `answer` | type `missing` |
| Wrong type | `"difficulty": 3` | type error |
| Rule violation | Empty list, bad enum value | constraint error |
| Not a validation error | Timeout, connection refused | A different exception; handle separately |

```python
import json

def classify_error(error: ValidationError) -> str:
    kinds = {e["type"] for e in error.errors()}
    return "invalid_json" if "json_invalid" in kinds else "schema_error"

def error_details(error: ValidationError) -> str:
    """Convert error details into plain text for logging (use inside an except block)."""
    return json.dumps(error.errors(include_url=False, include_context=False), default=str)
```

Keep these short. The `errors()` method returns a list of dictionaries describing each problem **[VERIFY argument names in your Pydantic version]**.

## 9. Bounded Retries **[ILLUSTRATIVE]**

A **retry** means asking the model again after a failure. It must be **bounded**: a fixed maximum number of attempts.

```python
MAX_ATTEMPTS = 3          # decide this value; keep it small


class StructuredOutputError(Exception):
    """Raised when no valid output was produced within MAX_ATTEMPTS."""


def get_structured_answer(call_model, prompt):
    """call_model(prompt) -> raw text. Returns (validated_object, attempts_used)."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):          # fixed range: cannot loop forever
        raw_text = call_model(prompt)
        try:
            return ExamQuestionSet.model_validate_json(raw_text), attempt
        except ValidationError as error:
            last_error = error
            log_failure(attempt, classify_error(error), len(raw_text))
    raise StructuredOutputError(f"Invalid after {MAX_ATTEMPTS} attempts") from last_error
```

Explanation:

- The `for` loop with `range(1, MAX_ATTEMPTS + 1)` makes an infinite loop impossible.
- Success returns immediately and reports which attempt worked.
- After the last failure, the function raises a clear error instead of pretending.
- The optional improvement is to add the error message to the next prompt ("Your last answer was invalid because ...") **[PLANNED to test: it may help or may not]**.

## 10. How to Prevent Infinite Retry Loops

1. Use a `for` loop over a fixed range, not `while True`.
2. Keep `MAX_ATTEMPTS` small and in the config file.
3. Also set a **timeout** on each model call so one attempt cannot hang forever.
4. Optionally set an **overall time budget** per task.
5. Do not retry errors that retrying cannot fix (for example "model not found" or "connection refused" from a stopped server). Retry a timeout at most once, and count that retry toward `MAX_ATTEMPTS` (full policy table in [ARCHITECTURE.md](./ARCHITECTURE.md#10-retry-mechanism)).
6. Add a test that proves the loop stops (see [TESTING_AND_EVALUATION.md](./TESTING_AND_EVALUATION.md)).
7. If a user can press "retry," count those separately and cap them too.

## 11. How to Log Validation Failures **[ILLUSTRATIVE]**

```python
import json
import logging
import time

logger = logging.getLogger("validation")

def log_failure(attempt: int, failure_type: str, raw_length: int) -> None:
    logger.warning(json.dumps({
        "time": time.time(),
        "attempt": attempt,
        "failure_type": failure_type,
        "raw_length": raw_length,       # length only, not the text itself
    }))
```

Privacy note: the model output might contain parts of confidential notes. By default, log **metadata** (counts, lengths, types), not full text. If you must log full text while debugging, store it in a protected local location and delete it afterwards (see [PRIVACY_AND_SECURITY.md](./PRIVACY_AND_SECURITY.md)).

## 12. How to Measure Structured-Output Reliability

For each model, over N structured test runs:

| Metric | Formula |
|---|---|
| First-attempt valid rate | valid on attempt 1 ÷ N |
| Eventual valid rate | valid within `MAX_ATTEMPTS` ÷ N |
| Retry rate | runs needing 2 or more attempts ÷ N |
| Average attempts | total attempts ÷ N |
| Failure breakdown | count of `invalid_json`, `schema_error`, `timeout`, `connection_error` |

**Always report the first-attempt rate.** A model that needs retries to look reliable is slower and costlier, and the eventual rate alone would hide that.

## 13. Four Different Kinds of "Correct"

| Level | Question it answers | Checked by | Example of passing but still wrong |
|---|---|---|---|
| 1. **Syntactic validation** | Is it well-formed JSON? | A JSON parser (also part of `model_validate_json`) | `{"capital": "Berlin"}` is perfectly formed. |
| 2. **Schema validation** | Does it have the required fields and types? | Pydantic | `{"country": "France", "capital": "Berlin"}` matches the schema. |
| 3. **Semantic correctness** | Does the content make sense for the task? (right topic, consistent, answerable) | Custom rules, a rubric, human review | A question about chemistry returned for a biology request. |
| 4. **Factual accuracy** | Is it true? | Human checking against reliable sources | The capital of France is Paris, not Berlin. |

> **Important:** Pydantic validation does **not** guarantee that an answer is factually correct. It only checks form (levels 1 and 2). Levels 3 and 4 need other methods: custom checks where possible, a quality rubric, and human review. Never describe a schema-valid answer as "verified" or "correct."

### Simple semantic checks you could add **[PLANNED]**

```python
from pydantic import field_validator

class ExamQuestion(BaseModel):
    question: str = Field(min_length=10)
    answer: str = Field(min_length=1)
    difficulty: Literal["easy", "medium", "hard"]

    @field_validator("question")
    @classmethod
    def must_look_like_a_question(cls, value: str) -> str:
        if not value.strip().endswith("?"):
            raise ValueError("question should end with a question mark")
        return value
```

This is still a *form* rule. It cannot tell whether the question is good or true.

## 14. Summary Checklist

- [ ] Output format described with a Pydantic schema
- [ ] Both JSON syntax and schema checked via Pydantic
- [ ] Failures classified (JSON, schema, timeout, connection)
- [ ] Retry loop bounded and tested
- [ ] First-attempt and eventual success rates both reported
- [ ] Logs avoid storing sensitive text by default
- [ ] Documentation says plainly that validation is not fact-checking
