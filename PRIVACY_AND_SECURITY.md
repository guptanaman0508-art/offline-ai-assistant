# Privacy and Security

[Back to README](./README.md)

> **Status:** design guidance and a verification plan. **None of the verification steps below has been run.** This document does not claim that the project is private or secure. It explains what local inference can and cannot do. Labels are explained in the [README](./README.md#read-this-first-status-legend). This is not legal or compliance advice.

---

## 1. The Core Message

**Local inference reduces reliance on external AI services, but it does not automatically guarantee complete privacy or security.**

Running a model on your own computer means your prompts do not *need* to be sent to an AI provider. Whether they actually stay local depends on your software, settings, network, files, and the people and programs with access to the machine. Treat "stays local" as a **claim to verify**, not a fact to assume.

## 2. Benefits and Limits at a Glance

| Area | Possible benefit of local inference | Remaining risk |
|---|---|---|
| Prompts and documents | Not sent to a third-party AI provider by design | Application bugs or settings may still send data out |
| Internet dependence | Can run offline after setup **[VERIFY]** | Model downloads and updates need internet |
| Control | You choose models and versions | You are responsible for patching and configuration |
| Logs | You decide what is logged | Logs may contain sensitive text |
| Access | Data stays on hardware you control | Anyone with access to the computer or backups may reach the data |

## 3. Local Model Execution

- Inference runs inside the Ollama process on your machine.
- Our Python application should send requests **only** to the local Ollama address (default `http://localhost:11434` **[VERIFY]**).
- The model files themselves are data on disk. Prompts are processed in memory.
- Memory can be written to disk (swap/page file, crash dumps, hibernation files). Disk encryption helps protect these (Section 7).

## 4. External Network Requests

Possible sources of outside traffic:

| Source | Why it matters | Action |
|---|---|---|
| `ollama pull` | Downloads models from a registry; reveals which model you downloaded | Expected; do it before handling private data |
| Ollama updates or desktop-app features | May contact online services **[VERIFY in current docs]** | Review settings; check connections |
| Cloud-hosted model options or web-search features in Ollama | Would send prompts to remote services **[VERIFY availability in your Ollama version]** | For private use, do not select such models or features |
| Our Python code | A bug or added library could call an external API | Code review; fewer dependencies |
| Third-party Python packages | May collect telemetry or have vulnerabilities | Review; pin versions; audit (Section 8) |
| Operating system and other software | Not part of our project but may sync files | Exclude project folders from cloud sync |

## 5. Ollama API Exposure and Network Configuration

- The Ollama API is designed for local use. **Do not assume it has authentication.** **[VERIFY in the current docs]**
- By default it should listen only on the loopback address (`127.0.0.1`). Binding to all network interfaces (for example setting the `OLLAMA_HOST` environment variable to `0.0.0.0`) could let other devices on your network use it **[VERIFY variable name and behavior]**.
- If you ever need remote access, put it behind an authenticated, encrypted proxy and a firewall, and treat that as a separate security project.
- Do not forward port 11434 through a router.
- On shared or public Wi-Fi, confirm binding before use.

Check what is listening (run the command that matches your OS **[VERIFY output on your system]**):

```bash
# Linux
ss -ltnp | grep 11434

# macOS
lsof -iTCP:11434 -sTCP:LISTEN

# Windows (PowerShell)
netstat -ano | findstr 11434
```

Expected for a local-only setup: the address shown is `127.0.0.1` (or `::1`), not `0.0.0.0` or a network address.

## 6. Sensitive Logs

- Application logs, benchmark CSVs, and error messages can hold confidential text.
- **Default rule [PLANNED]:** log metadata (timestamps, lengths, counts, failure types) rather than prompts or answers.
- If full text is needed for debugging, enable it temporarily, store it in a protected folder, and delete it afterwards.
- Keep benchmark prompts free of real confidential data; use made-up or public text.
- Exclude logs and results from version control (`.gitignore`).
- Be aware that tools such as shell history, IDE history, and backups may also capture text.

## 7. Document Storage

- Keep notes in a dedicated folder with restricted OS permissions.
- Do not store private notes in the Git repository, and do not upload the repository with private files.
- Avoid cloud-synced folders (OneDrive, iCloud, Dropbox, Google Drive) for sensitive documents unless you accept that sync.
- Use full-disk encryption (BitLocker on Windows, FileVault on macOS, LUKS or equivalent on Linux) **[VERIFY availability for your edition]**.
- Remember that temporary files, backups, and recycle bins keep copies.

## 8. Dependency Security

- Use a virtual environment and a `requirements.txt` with **pinned versions**.
- Install only packages you need (we keep the stack small on purpose).
- Install from the official package index; check the package name carefully to avoid look-alike (typosquatted) packages.
- Check packages for known vulnerabilities with a tool such as `pip-audit` **[VERIFY usage]**.
- Update deliberately and re-test after updates.
- Keep Ollama and the operating system updated, and read release notes for security fixes.

## 9. Model Provenance and Licensing

- **Provenance:** download models from the official Ollama library or the model publisher. Record the exact tag and, if available, the model digest shown by `ollama show` / `ollama list` **[VERIFY]**. Avoid unknown or unofficial model files; model files can be a risk if obtained from untrusted sources.
- **Open-source software vs open-weight models:** Ollama and most Python libraries are open-source software. Models are separate works with separate licenses. "Open-weight" means the weights can be downloaded; it does not necessarily mean unrestricted use.
- **Do not assume all models share terms.** Some licenses restrict commercial use, require attribution, or include acceptable-use policies. Read each one.
- Record license name, link, and key restrictions per model:

| Model | License name | Link | Key restrictions to note | Suitable for our use? |
|---|---|---|---|---|
| Model A | TBD | TBD | TBD | TBD |
| Model B | TBD | TBD | TBD | TBD |
| Model C | TBD | TBD | TBD | TBD |

- For organizations such as law firms, have legal or compliance staff review licenses before any real use.

## 10. Access Control

- Use a separate OS user account on shared computers; lock the screen.
- Give notes, logs, and results folders restricted permissions.
- Remember that any local program running as your user may be able to call the local Ollama API and read your files.
- The prototype has no user authentication. Multi-user or office use would require authentication, authorization, and audit logging, which are **out of scope**.

## 11. Data Retention

Decide and document:

| Data | Where it may exist | Planned retention rule |
|---|---|---|
| Prompts and answers | Memory; maybe logs | Not stored by default; delete debug logs promptly |
| Notes | Local notes folder | Owner-controlled |
| Benchmark results | `results/` | Contain metadata only; safe to keep if no private text |
| Model files | Ollama's model storage | Remove unused models with `ollama rm` |
| Backups | OS backup tools | Check what is included |

Deleting a file normally does not erase it securely from the disk; full-disk encryption reduces this risk.

## 12. Risk Summary

| Risk | Likelihood (to assess) | Impact (to assess) | Mitigation |
|---|---|---|---|
| App sends data to an external service | TBD | High | Code review; network checks |
| Ollama exposed to network | TBD | High | Check binding; firewall |
| Sensitive text in logs | TBD | Medium to High | Metadata-only logging |
| Vulnerable dependency | TBD | Medium | Pin, audit, update |
| Untrusted model file | TBD | Medium to High | Official sources only |
| Lost or stolen laptop | TBD | High | Disk encryption; screen lock |
| Model hallucination used as fact | High | Medium | Human review; clear UI warnings |
| License violation | TBD | Medium | Read and record licenses |

Likelihood and impact are placeholders; fill them in with your mentor.

## 13. How to Verify That the Application Does Not Send Prompts or Documents to an External AI Provider **[PLANNED; not yet performed]**

No single check proves this. Combine several.

**Check 1: Code review.**
Search the project for network-related code and URLs:

```bash
# macOS / Linux
grep -rniE "http|requests|urllib|socket|api[_-]?key|openai|anthropic|cloud" src/

# Windows PowerShell
Select-String -Path src\*.py -Pattern "http|requests|urllib|socket|api_key|openai|anthropic|cloud"
```

Expected: the only host is the local Ollama address (and it is configurable in one place). No API keys, no unknown URLs.

**Check 2: Dependency review.**
List installed packages (`pip list`) and confirm each is needed. Review any that handle networking.

**Check 3: Offline test.**
After models are downloaded, disconnect from the network (turn off Wi-Fi, unplug Ethernet), then run the assistant on a test note. Expected: it still works. If it fails, find out why. Note: a local connection to `localhost` does not need the internet **[VERIFY on your system]**.

**Check 4: Inspect active connections while running.**
While the app is processing a prompt, list network connections and look for unexpected remote addresses:

```bash
# Linux
ss -tpn

# macOS
lsof -i -nP

# Windows (PowerShell)
netstat -ano
```

Expected: connections between our app and Ollama on `127.0.0.1:11434`; no connections from the Python process or Ollama to unknown external addresses. Interpret carefully: other programs on the computer also make connections, and you must match connections to the right process. A short snapshot can miss brief connections.

**Check 5: Firewall block test.**
Create an outbound firewall rule that blocks the Python executable and, separately, the Ollama executable from non-local destinations. Run the assistant. Expected: it still works. **[VERIFY firewall steps for your OS]**

**Check 6: Packet capture (optional, advanced).**
A tool such as Wireshark or `tcpdump` can record traffic while you run a task with a unique marker phrase in the note. Expected: the marker does not appear in outbound external traffic. Encrypted traffic cannot be read, so also check destinations. Only capture traffic on your own machine and network.

**Check 7: Marker test for storage.**
Use a unique fake phrase (for example `ZEBRA-PINEAPPLE-0001`) in a test note. After running, search logs, results, and the repository for it. Expected: it appears only where you intentionally allow it.

**Check 8: Review Ollama's own behavior.**
Read the current Ollama documentation and privacy statements for telemetry, update checks, and cloud features. Run Checks 3 to 5 with Ollama in the same state you will use it **[VERIFY, since behavior can change between versions]**.

Document each check with date, version numbers, and result, using the execution log in [TESTING_AND_EVALUATION.md](./TESTING_AND_EVALUATION.md#14-execution-log-fill-in-when-you-run-tests). If a check cannot be performed, write "not performed", not "passed."

## 14. Privacy Testing Summary

| Test | Purpose | Status |
|---|---|---|
| Code review | Find unexpected network calls | Designed, not executed |
| Offline run | Show it works without internet | Designed, not executed |
| Connection inspection | Detect unexpected remote connections | Designed, not executed |
| Binding check | Confirm Ollama is not exposed | Designed, not executed |
| Marker test | Find where text is stored | Designed, not executed |
| Firewall block test | Confirm no hidden dependency on outside access | Designed, not executed |

## 15. What We Will Not Claim

- That the system is "100% secure" or "fully private."
- That local models never leak data.
- That the prototype meets any legal, regulatory, or professional confidentiality requirement.
- That all open-weight models may be used for any purpose.

What we *can* say once verified: "In our tests, on our setup, with these versions, we observed no prompt or document data being sent to an external AI provider, and we describe the checks we performed and their limits."

## 16. Recommendations for Organizations (Beyond This Prototype)

A law firm or business would additionally need: a risk assessment, legal and compliance review, access control and authentication, audit logging, encrypted storage, managed devices and updates, a vetted list of approved models and licenses, incident response procedures, and staff training. This project does not provide these.
