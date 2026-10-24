# FAQ and Mentor Preparation

[Back to README](./README.md)

> **Status:** preparation material for a project that is **still in the planning stage**. Answers describe the *plan* ("we will measure...") and general technical facts. Do not say anything is built, tested, or measured until it really is. Labels are explained in the [README](./README.md#read-this-first-status-legend).

**How to use this:** read each answer, then close the document and explain it in your own words. Mentors usually prefer a short, honest answer ("we plan to... and we have not tested it yet") over a confident but unproven one.

**60-second summary you can say aloud:**
"I am building a Python program that uses Ollama to run open-weight language models on my own computer. I will compare three models on speed, memory, answer quality, and how reliably they produce valid JSON checked by Pydantic, with limited retries. The first use is a semester-notes assistant. Local processing reduces dependence on external AI services, but I do not claim it guarantees complete security. So far I have written the plan and documentation."

---

## Section A: AI and ML Fundamentals

**Q1. What is Artificial Intelligence?**
AI is the broad field of making computers do tasks that normally need human intelligence, such as understanding language, recognizing images, or making decisions.

**Q2. What is Machine Learning?**
ML is a part of AI where a program learns patterns from data instead of following only hand-written rules.

**Q3. What is Deep Learning?**
Deep learning is a kind of machine learning that uses large neural networks with many layers. Modern LLMs are deep-learning models.

**Q4. What is Generative AI?**
Generative AI creates new content (text, images, code) based on patterns learned from training data. An LLM generating an answer is generative AI.

**Q5. What is the difference between training and inference?**
Training builds the model by adjusting its weights using lots of data. Inference uses the finished model to produce outputs. This project only does inference.

**Q6. What is a hallucination?**
A hallucination is a confident-sounding answer that is false or invented. It happens because LLMs predict likely text; they do not automatically verify facts.

## Section B: LLMs and Local Inference

**Q7. What is an LLM?**
A Large Language Model is a model trained on massive text data to predict the next token in a sequence. By doing this repeatedly, it can answer, explain, and summarize.

**Q8. What is local inference?**
Running a trained model on your own computer (CPU and optionally GPU) rather than sending the request to a remote server.

**Q9. What is an open-weight model?**
A model whose trained weights are released so you can download and run them. "Open-weight" is not the same as fully open source: training data or code may not be shared, and each model has its own license terms.

**Q10. What is a token?**
A token is a small chunk of text (part of a word, a whole short word, or punctuation) that the model reads and writes. Roughly, English text averages a bit under one word per token, but this varies **[VERIFY per model's tokenizer]**.

**Q11. What is a context window?**
The maximum amount of text (in tokens) the model can consider at once, including your prompt and its answer. Notes longer than that must be shortened or split.

**Q12. What is quantization?**
Quantization stores the model's numbers with fewer bits (for example, 4 bits instead of 16). This makes the model smaller and often faster to run, but may slightly reduce quality.

**Q13. Does running locally make the model smarter or better?**
No. Local running changes *where* it runs, not how capable it is. Small local models are often less capable than the largest hosted models.

## Section C: Ollama

**Q14. Is Ollama an AI model?**
No. Ollama is software that downloads, manages, and runs models and offers a local API. The model is a separate file.

**Q15. Why use Ollama?**
It simplifies local use: one command to download a model, automatic loading, and a ready-made local API that Python can call. It avoids building the inference setup ourselves.

**Q16. Where does Ollama run and how does Python talk to it?**
Ollama runs as a local server, by default on `localhost` port 11434 **[VERIFY]**. Python sends HTTP requests (directly or through the `ollama` library) and receives the response.

**Q17. Does Ollama need the internet?**
Downloading models needs internet. After a model is downloaded, running it should not **[VERIFY on your setup]**. Some Ollama features may use online services (for example cloud-hosted models); we avoid those for private use **[VERIFY in current docs]**.

**Q18. What does `ollama ps` show?**
Which models are currently loaded in memory, their memory size, and where they are running (CPU/GPU) **[VERIFY output format]**.

## Section D: Python Integration

**Q19. How will Python use the model?**
Our program builds a prompt, sends it to the Ollama server through the `ollama` library (or HTTP), waits with a timeout, and receives text plus timing counters.

**Q20. What is an API and an endpoint?**
An API is a defined way for programs to talk to each other. An endpoint is one specific address of an API, like `/api/chat`.

**Q21. What is streaming and why does it matter?**
With streaming, the answer arrives in pieces as generated. We need it to measure time to first token.

**Q22. Why use a virtual environment?**
It keeps this project's packages separate from other projects, avoiding version conflicts and making the setup reproducible.

**Q23. What happens if Ollama is not running or the model is missing?**
The application should catch the error and show a clear message ("start Ollama" or "run `ollama pull <tag>`"), not crash. This is a planned test case.

## Section E: Model Benchmarking

**Q24. What is a benchmark?**
A controlled, repeatable measurement used to compare options fairly.

**Q25. Why compare three models?**
Models trade off speed, memory, quality, and reliability. Three gives enough variety to see trade-offs while staying manageable for a first project. The number is a scope decision, not a scientific rule.

**Q26. How will you choose the three models?**
After checking hardware, memory budget, Ollama compatibility, and licenses; then documenting exact tags and reasons. We have not chosen them yet.

**Q27. What is latency?**
The waiting time between asking and receiving. We split it into time to first token and total response time.

**Q28. What is the difference between time to first token and total response time?**
Time to first token is how long until the first output appears. Total response time is how long until the answer is complete, which also depends on answer length.

**Q29. What is tokens per second?**
How many output tokens the model generates each second: `eval_count ÷ eval_duration (in seconds)` using Ollama's reported counters **[VERIFY]**. Higher is faster.

**Q30. How will RAM usage be measured?**
By observing the Ollama process memory with `psutil` and cross-checking with `ollama ps` and the operating system's monitor, comparing baseline and peak. Model file size is *not* the same as RAM use; context length, quantization, and workload change it.

**Q31. How will answer quality be evaluated?**
With a written rubric (correctness, completeness, clarity, faithfulness, instruction-following) applied to a fixed dataset, scored blind, with a consistency check. The method is defined before testing.

**Q32. Why are warm-up runs and repeated trials needed?**
The first request includes model loading, and timing varies from run to run. Warm-ups remove load time from measured results; repeats reveal variation and let us report medians.

**Q33. Can you declare an overall "best" model?**
No. "Best" depends on priorities (quality, speed, memory, license) and on this hardware and dataset. We will state conclusions narrowly.

## Section F: Pydantic and JSON

**Q34. What is JSON?**
A text format for structured data with objects, lists, strings, numbers, booleans, and null.

**Q35. What is Pydantic?**
A Python library that checks data against a defined structure and turns valid data into typed objects.

**Q36. What is schema validation?**
Checking that data has the required fields, correct types, and allowed values according to a schema.

**Q37. Does Pydantic verify factual correctness?**
No. It checks form only. A well-formed, schema-valid answer can still be false, off-topic, or misleading.

**Q38. Why not just ask the model to "reply in JSON" and trust it?**
Models sometimes add extra text, break syntax, or omit fields. Validation catches this before the data reaches the rest of the program.

## Section G: Validation and Retry Logic

**Q39. What is retry logic?**
When validation fails, ask the model again. Because outputs vary, a second attempt may succeed.

**Q40. How do you prevent infinite retry loops?**
Use a `for` loop with a fixed maximum number of attempts, per-call timeouts, no retries for unrecoverable errors, and a test proving the loop ends.

**Q41. How do you measure structured-output reliability?**
Count first-attempt valid rate, eventual valid rate, retry rate, average attempts, and failure types for each model. Report first-attempt results so retries do not hide weakness.

**Q42. Do retries make the answer more accurate?**
Not necessarily. They can fix *format* problems. A retry may produce a valid but still wrong answer.

## Section H: Privacy and Security

**Q43. Does local AI guarantee complete security?**
No. It reduces reliance on external AI services, but risks remain: logs, stored files, malware, a mis-exposed Ollama port, vulnerable dependencies, untrusted model files, shared computers, and backups.

**Q44. How will you verify that prompts are not sent to an outside AI provider?**
Planned checks: code review for network calls, running with the network disabled after models are downloaded, inspecting network connections while the app runs, and confirming Ollama listens only on localhost. See [PRIVACY_AND_SECURITY.md](./PRIVACY_AND_SECURITY.md). These checks have not been run yet.

**Q45. What data might still leak?**
Log files, saved results, copied notes, crash dumps, backups, and cloud-synced folders.

**Q46. Are open-weight models free to use however you like?**
Not necessarily. Each license has its own terms, such as limits on commercial use or required acknowledgements. We will read and record each license.

## Section I: Project Architecture

**Q47. Can you explain the architecture in one minute?**
The user talks to a Python app. The app validates input, builds a prompt, and calls the local Ollama server. The server runs the selected model and returns text. For structured tasks, Pydantic validates it and a bounded retry loop handles failures. The benchmark runner repeats a fixed dataset across three models, measures performance, evaluates quality, and writes CSV results. (See [ARCHITECTURE.md](./ARCHITECTURE.md).)

**Q48. What makes this different from a basic chatbot?**
It adds measurement and comparison of multiple models, validated structured output with bounded retries, a defined quality-evaluation method, privacy verification steps, and honest documentation of limits.

**Q49. Why CSV for results?**
It is simple, human-readable, works in any spreadsheet, and is enough for this scale. A database would add unnecessary complexity.

**Q50. Are we training our own model?**
No. We use existing open-weight models for inference only. Training or fine-tuning is out of scope.

**Q51. Why avoid extra frameworks?**
Fewer dependencies mean fewer things to learn, fewer bugs, and a smaller security surface.

## Section J: Limitations and Future Improvements

**Q52. What are the limitations of this project?**
Results apply only to our hardware, models, prompts, and settings; three models are a small sample; quality scoring is partly subjective; local models can be weaker than the largest hosted ones; validation does not check facts; local inference does not guarantee security. See the Limitations sections in [README.md](./README.md#20-limitations) and [MODEL_BENCHMARK.md](./MODEL_BENCHMARK.md#15-benchmark-limitations).

**Q53. What has actually been done so far?**
Only planning and documentation. Say this plainly; update this answer as real work is completed.

**Q54. What would you improve next?**
Retrieval over long notes, a simple interface, more models and hardware, better evaluation methods, and stronger privacy hardening.

**Q55. What if two models score almost the same?**
Call it a tie on that metric and decide using other factors, such as memory use, license, or structured-output reliability.

**Q56. How could this help law firms or businesses?**
It is a learning prototype showing how local processing can reduce exposure of confidential text to external AI services. A real deployment would need security review, legal and compliance input, access control, and auditing.

---

## Questions to Ask Your Mentor

1. Is three models the right scope, or should we compare sizes within one family?
2. Is our quality rubric sufficient, or should another person score as well?
3. How strong must privacy verification be for the final report?
4. What should we prioritize if time runs short: more models, more tests, or better documentation?
5. Which results would make this project convincing to you?
