# Glossary

[Back to README](./README.md)

> **Status:** reference document. Examples are explanatory, not measurements from this project. Labels such as **[VERIFY]** are explained in the [README](./README.md#read-this-first-status-legend).

Each term has: **Definition** (simple), **Example** (practical), and **Why it matters here**.

**Contents:** [AI](#artificial-intelligence-ai) · [ML](#machine-learning-ml) · [Deep Learning](#deep-learning) · [Generative AI](#generative-ai) · [LLM](#llm-large-language-model) · [Open-weight model](#open-weight-model) · [Inference](#inference) · [Local inference](#local-inference) · [Ollama](#ollama) · [Token](#token) · [Tokenization](#tokenization) · [Prompt](#prompt) · [Context window](#context-window) · [Quantization](#quantization) · [RAM](#ram) · [VRAM](#vram) · [Latency](#latency) · [Throughput](#throughput) · [Tokens per second](#tokens-per-second) · [Benchmark](#benchmark) · [Dataset](#dataset) · [Pydantic](#pydantic) · [JSON](#json) · [Schema](#schema) · [Validation](#validation) · [Retry logic](#retry-logic) · [API](#api) · [Endpoint](#endpoint) · [CSV](#csv) · [Model evaluation](#model-evaluation) · [Hallucination](#hallucination) · [Structured output](#structured-output)

---

## Artificial Intelligence (AI)
- **Definition:** The broad field of building computer systems that perform tasks that usually need human intelligence, such as understanding language or recognizing patterns.
- **Example:** A program that answers questions about your notes.
- **Why it matters here:** Our assistant is an AI application; the field provides the vocabulary for the whole project.

## Machine Learning (ML)
- **Definition:** A part of AI where computers learn patterns from data instead of being given every rule by hand.
- **Example:** An email filter that learns what spam looks like from many examples.
- **Why it matters here:** LLMs are produced by machine learning; we use a finished model and do not train one.

## Deep Learning
- **Definition:** A type of machine learning using large neural networks with many layers.
- **Example:** Systems that recognize speech or generate text use deep learning.
- **Why it matters here:** The models we run in Ollama are deep-learning models, which is why they are large and need a lot of memory.

## Generative AI
- **Definition:** AI that creates new content such as text, images, or code.
- **Example:** Writing a summary of your lecture notes.
- **Why it matters here:** Our assistant generates answers, summaries, and exam questions, so it can produce errors and must be checked.

## LLM (Large Language Model)
- **Definition:** A model trained on large amounts of text to predict the next token, which lets it produce human-like text.
- **Example:** Given "Water boils at 100 degrees", it can continue with "Celsius at sea level".
- **Why it matters here:** The LLM is the core "brain." We compare three of them.

## Open-weight model
- **Definition:** A model whose trained weights can be downloaded and run by anyone who accepts its license. It is not automatically "open source": data and code may be unavailable, and licenses can restrict use.
- **Example:** A model you can fetch with `ollama pull`.
- **Why it matters here:** Running models locally requires downloadable weights, and every model's license must be read separately.

## Inference
- **Definition:** Using a trained model to produce an output from an input.
- **Example:** Asking a model a question and receiving an answer.
- **Why it matters here:** Everything we do is inference; we do not train models.

## Local inference
- **Definition:** Running inference on your own computer instead of a remote server.
- **Example:** Your laptop produces the answer with no request to an online AI service.
- **Why it matters here:** It is the basis of the privacy goal, but it does not guarantee complete security.

## Ollama
- **Definition:** Software that downloads, manages, and runs open-weight models locally and provides a local API.
- **Example:** `ollama pull <tag>` downloads a model; `ollama run <tag>` chats with it.
- **Why it matters here:** It is the runtime between our Python program and the models. It is *not* a model itself.

## Token
- **Definition:** A small unit of text (a word, part of a word, or punctuation) that an LLM reads and writes.
- **Example:** "unbelievable" may be split into several tokens.
- **Why it matters here:** Speed (tokens per second), context limits, and output length are all measured in tokens.

## Tokenization
- **Definition:** Converting text into tokens (and back).
- **Example:** The sentence "Hello world" becomes a short list of token IDs.
- **Why it matters here:** Different models tokenize differently, so token counts are not exactly comparable between models.

## Prompt
- **Definition:** The input text given to a model, including instructions and any supplied content.
- **Example:** "Summarize these notes in 3 bullet points: ..."
- **Why it matters here:** Fair benchmarking requires the same prompts for every model. Prompt wording affects quality and format reliability.

## Context window
- **Definition:** The maximum number of tokens (input plus output) a model can handle at once.
- **Example:** If your notes are longer than the window, the model cannot see all of them.
- **Why it matters here:** It limits note length and affects memory use; we must set and record the context length.

## Quantization
- **Definition:** Storing model numbers with fewer bits to make the model smaller and often faster, sometimes at some cost to quality.
- **Example:** A 4-bit version of a model is smaller than its 16-bit version.
- **Why it matters here:** It explains differences between model tags and between file size and quality; it must be recorded for fair comparison.

## RAM
- **Definition:** Random Access Memory, the computer's fast working memory.
- **Example:** A laptop with 16 GB of RAM can hold limited model data at once.
- **Why it matters here:** Loaded models occupy memory; too little RAM causes slowness or failure. We measure RAM usage.

## VRAM
- **Definition:** Video RAM, the memory on a graphics card (GPU).
- **Example:** A GPU with limited VRAM may only fit smaller models, so part of the model may run on the CPU.
- **Why it matters here:** On computers with a GPU, VRAM often decides which models run fast. On some computers the CPU and GPU share memory **[VERIFY for your hardware]**.

## Latency
- **Definition:** The waiting time before a response arrives.
- **Example:** Two seconds until the answer begins appearing.
- **Why it matters here:** We separate time to first token from total response time.

## Throughput
- **Definition:** How much work is done per unit of time.
- **Example:** Tokens generated per second, or questions answered per minute.
- **Why it matters here:** Latency measures one request's waiting; throughput measures speed or capacity. We report tokens per second.

## Tokens per second
- **Definition:** Number of output tokens generated each second.
- **Example:** 200 tokens in 10 seconds is 20 tokens per second (arithmetic example only, not a measurement).
- **Why it matters here:** A key speed metric, computed from Ollama's counters **[VERIFY]**. Interpret it with answer length.

## Benchmark
- **Definition:** A controlled, repeatable test used to compare things fairly.
- **Example:** Running the same 30 prompts on three models and recording times.
- **Why it matters here:** It turns opinions into evidence for choosing a model.

## Dataset
- **Definition:** A collection of data, here a fixed set of test prompts with reference key points.
- **Example:** `benchmark_prompts.json` with 30 entries.
- **Why it matters here:** The same dataset for all models ensures fairness and repeatability.

## Pydantic
- **Definition:** A Python library that validates data against a defined structure.
- **Example:** Checking that every exam question has a `question`, an `answer`, and a valid `difficulty`.
- **Why it matters here:** It detects bad structured output. It does **not** check facts.

## JSON
- **Definition:** A text format for structured data using objects, lists, strings, numbers, booleans, and null.
- **Example:** `{"topic": "Cells", "questions": []}`
- **Why it matters here:** It is how the model returns data our program can read.

## Schema
- **Definition:** A description of what valid data must look like: fields, types, and rules.
- **Example:** "`difficulty` must be easy, medium, or hard."
- **Why it matters here:** It defines what "valid output" means.

## Validation
- **Definition:** Checking whether data meets defined rules.
- **Example:** Parsing JSON and checking required fields. (Syntactic and schema validation are different from factual accuracy.)
- **Why it matters here:** It catches malformed output before the program uses it.

## Retry logic
- **Definition:** Code that tries again after a failure, within a fixed limit.
- **Example:** Ask the model up to 3 times for valid JSON, then stop.
- **Why it matters here:** It improves reliability, but it must be bounded and measured, so it does not hide weak models or loop forever.

## API
- **Definition:** Application Programming Interface: a defined way for programs to communicate.
- **Example:** Python sends a request to Ollama and receives a response.
- **Why it matters here:** The Ollama API is how our application uses the models.

## Endpoint
- **Definition:** A specific address of an API that performs one function.
- **Example:** `/api/chat` for chat requests, `/api/tags` for listing models **[VERIFY]**.
- **Why it matters here:** We use endpoints to check models and run prompts.

## CSV
- **Definition:** Comma-Separated Values, a plain-text table format.
- **Example:** `model_tag,total_s` on the first line, then one row per run.
- **Why it matters here:** Our raw and summary benchmark results are stored as CSV and can be opened in a spreadsheet.

## Model evaluation
- **Definition:** Judging how well a model performs, using a defined method.
- **Example:** Scoring answers 0 to 2 on correctness, completeness, clarity, faithfulness, and instruction-following.
- **Why it matters here:** Quality cannot be assumed; the method must be defined before testing and applied fairly.

## Hallucination
- **Definition:** An answer that sounds confident but is false or invented.
- **Example:** Citing a book that does not exist.
- **Why it matters here:** Valid format does not prevent hallucination; our evaluation includes a faithfulness check and human review.

## Structured output
- **Definition:** Model output in a predefined, machine-readable format.
- **Example:** A JSON list of exam questions instead of free paragraphs.
- **Why it matters here:** It lets the program process results reliably; we measure how often each model produces valid structured output.
