# Offline AI Assistant and Model Benchmark

A small Python command-line assistant that chats with locally installed language models through [Ollama](https://ollama.com), plus a benchmark tool for comparing model latency, generation speed, memory use, and structured-output reliability on your own machine.

The project is intended for learning and local experimentation. It does not upload prompts to a hosted AI API by design, but local execution alone is not a guarantee of privacy or security; review your Ollama configuration, machine, logs, and model license before using sensitive material.

## Features

- Interactive multi-turn terminal chat with a selectable Ollama model.
- Local model/server availability checks and request latency display.
- Conversation reset and clean exit commands.
- Repeatable benchmark runs over a bundled prompt set, with optional warm-up and repeated trials.
- Optional JSON output validation against a Pydantic schema, with at most three attempts.
- Raw benchmark records and per-model summary CSV exports.
- Unit tests for the client wrapper, validation/retries, benchmark calculations, and related behavior.

**Not implemented:** reading or indexing personal notes, retrieval-augmented generation (RAG), a graphical interface, and automatic answer-quality scoring. The quality field is left blank for manual evaluation using [`data/EVALUATION_RUBRIC.md`](data/EVALUATION_RUBRIC.md).

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/download) installed and running locally
- At least one Ollama model downloaded (the chat default is `llama3.2:3b`)

The Python dependencies are listed in [`requirements.txt`](requirements.txt): the Ollama Python client, Pydantic, and psutil. Model downloads require internet access; inference can run locally once the model is available.

## Setup

1. Install Python and Ollama for your operating system. Start Ollama (the desktop application normally starts the server automatically; alternatively run `ollama serve` in a terminal).
2. From the project root, create and activate a virtual environment:

   **macOS / Linux**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install the project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Download a model and confirm that it is installed:

   ```bash
   ollama pull llama3.2:3b
   ollama list
   ```

   If needed, check the local Ollama server with `ollama --version` and `curl http://localhost:11434/api/tags`.

## Usage

### Chat

Start the assistant with its default model:

```bash
python src/app.py
```

Select a different model that is already installed:

```bash
python src/app.py --model mistral:latest
# Equivalent short option:
python src/app.py -m mistral:latest
```

Type a question at the `You:` prompt. The assistant keeps conversation history for the current run and displays the response latency. Type `clear` to reset the conversation, or `exit`, `quit`, `/bye`, or `:q` to leave. Press `Ctrl+C` to interrupt.

The assistant sends chat requests to the local Ollama server (default `http://localhost:11434`). Ensure the selected model is pulled first; the application reports a helpful error if Ollama is unavailable or the model is missing.

### Benchmark

The benchmark runs the bundled five-prompt dataset against the default model tags:

```bash
python src/benchmark.py
```

Specify models and repeat each prompt for multiple trials:

```bash
python src/benchmark.py \
  --models llama3.2:3b qwen2.5:3b mistral:latest \
  --trials 3
```

Available options:

| Option | Purpose |
|---|---|
| `--models`, `-m` | Space-separated Ollama model tags; defaults to `llama3.2:3b qwen2.5:3b mistral:latest`. |
| `--trials`, `-t` | Measured repetitions per prompt and model; defaults to `1`. |
| `--prompts`, `-p` | Use a different JSON prompt dataset; defaults to `data/benchmark_prompts.json`. |
| `--no-warmup` | Skip the initial warm-up request for each available model. |
| `--structured`, `-s` | Request JSON and validate it against the Pydantic schema, retrying up to three total attempts. |

For example, run structured-output trials with two installed models:

```bash
python src/benchmark.py \
  --models llama3.2:3b qwen2.5:3b \
  --trials 2 \
  --structured
```

The benchmark records raw runs in `results/raw_runs.csv` (appending rows on subsequent runs) and regenerates `results/summary.csv`. The summary excludes warm-up rows from measured statistics. Unavailable models are skipped and recorded. Raw results can include response previews and error text; keep them out of version control and inspect them before sharing. Both CSV outputs are ignored by Git by default.

Benchmark measurements depend on the machine, Ollama version, model tag, and system load. Token-rate and model timing fields depend on metadata returned by Ollama and can be unavailable for some responses. Structured validity measures format/schema adherence, not truth or answer quality. Score responses manually against the rubric; do not treat unscored values as measured quality.

### Backend REST API

Start the local FastAPI backend with Uvicorn:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

#### Endpoints overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check backend operational status and Ollama daemon connectivity. |
| `GET` | `/models` | List locally installed models in Ollama (`models`, `count`). |
| `POST` | `/chat` | Send a prompt (`message`, optional `model`, optional `session_id`). |
| `DELETE` | `/chat/history` | Clear conversation history for a specific `session_id` or all sessions. |
| `GET` | `/metrics` | Retrieve host CPU/RAM specs and current Ollama daemon memory (RSS MB). |

#### Example Request and Response (`POST /chat`)

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain binary search in one sentence.",
    "model": "llama3.2:3b"
  }'
```

**Response:**
```json
{
  "session_id": "7f093374-bd9a-41d6-848e-6e84cfbf659b",
  "model": "llama3.2:3b",
  "response": "Binary search is an algorithm that repeatedly halves a sorted search interval to locate a target element in logarithmic time.",
  "latency_seconds": 1.24
}
```

> **Session Isolation Note:** Multi-turn conversation histories are stored in-memory partitioned by `session_id`. When the backend application process restarts, in-memory sessions are cleared. No persistent database or cloud storage is used.

### React Frontend Application

A modern, responsive dark-themed UI built with React, Vite, TypeScript, and Tailwind CSS is available in the `frontend/` directory.

#### Installation and Startup

1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The web UI will be available at `http://127.0.0.1:5173`.

3. Build for production:
   ```bash
   npm run build
   ```

#### Configuration

The frontend connects to the FastAPI backend using the environment variable `VITE_API_BASE_URL` (configured in `frontend/.env`, default: `http://127.0.0.1:8000`).

### Run tests


The test suite uses Python's built-in `unittest` runner or `pytest`. Mocked unit tests do not require a running Ollama server:

```bash
# Using pytest
pytest -v

# Or using unittest
python -m unittest discover -s tests -v
```

## Project layout

```text
.
├── src/
│   ├── api/                # FastAPI backend REST API
│   │   ├── __init__.py
│   │   ├── main.py         # Application entry point and route handlers
│   │   ├── schemas.py      # Request/response Pydantic schemas
│   │   └── session_manager.py # In-memory isolated session history manager
│   ├── app.py              # Interactive chat CLI
│   ├── benchmark.py        # Benchmark runner and CSV output
│   ├── evaluation.py       # JSON validation and bounded retries
│   ├── metrics.py          # Hardware, memory, and generation metrics
│   ├── ollama_client.py    # Ollama SDK wrapper
│   └── schemas.py          # Pydantic response schema
├── data/
│   ├── benchmark_prompts.json
│   └── EVALUATION_RUBRIC.md
├── results/                # Generated benchmark CSV files
├── scripts/                # Utility scripts (e.g. export_eval_responses.py)
├── tests/                  # Automated tests (unit, benchmark, and API)
├── requirements.txt
└── *.md                    # Project and design documentation
```

## Contributing

Contributions that improve the current CLI, benchmark correctness, tests, or documentation are welcome.

1. Fork or create a working branch and keep each change focused.
2. Read the relevant implementation and documentation before changing behavior. Avoid describing planned features as available.
3. Add or update unit tests for code changes, then run `python -m unittest discover -s tests -v`.
4. For changes involving Ollama or a real model, verify the behavior locally and document the model/version used; mocked tests alone do not establish end-to-end behavior.
5. Update the README or related documentation when commands, output formats, requirements, or behavior change.
6. Do not commit `.venv`, credentials, private notes, logs, or generated benchmark CSVs. Use public or synthetic prompts in examples and review benchmark output for sensitive text before sharing.
7. In a pull request, explain the problem, the change, how it was tested, and any limitations or model-specific assumptions.

There is no contribution license or code-style configuration in the current repository; do not assume a license for the project or for downloaded models. Check each model's terms before use or redistribution.

## Further documentation

- [Project overview](PROJECT_OVERVIEW.md)
- [Architecture](ARCHITECTURE.md)
- [Benchmark methodology](MODEL_BENCHMARK.md)
- [Structured output and validation](PYDANTIC_AND_VALIDATION.md)
- [Testing and evaluation](TESTING_AND_EVALUATION.md)
- [Privacy and security](PRIVACY_AND_SECURITY.md)
- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md)
- [FAQ and mentor preparation](FAQ_AND_MENTOR_PREPARATION.md)
- [Glossary](GLOSSARY.md)
