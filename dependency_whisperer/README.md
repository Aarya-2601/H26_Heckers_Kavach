# 🧠 Gemma 4 Dependency Whisperer (Person 3 Deliverable)

> **Track 1: Gemma 4 : Dependency Resilience**  
> AI-powered developer tool connecting automated dependency risk triage, AST-guided replacement synthesis, dual-set compatibility testing, and self-healing repair loops for Python software repositories.

---

## 🎯 What Person 3 Delivers

Person 3 (**The AI Whisperer**) is the intelligent core of the dependency migration pipeline. It connects static repository analysis (from Person 2) with sandbox test execution (from Person 1) and exit capsule presentation (from Person 4).

### Key Features
1. **Model Governance & Track 1 Compliance**:
   - **Model**: `gemma-4-it` / `gemma-2-9b-it`
   - **Version**: `4.0.0-preview`
   - **Access Method**: Hosted API (Google AI Studio / GenAI), local Ollama/vLLM endpoints, and a built-in zero-latency **Deterministic Mock Engine**.
   - **Terms**: Compliant with [Google Gemma Terms of Use](https://ai.google.dev/gemma/terms).
2. **Strict Evidence Separation (`[OBSERVED]` vs `[AI-SUGGESTED]`)**:
   - Every metric and recommendation is tagged by code (`TagEnum.OBSERVED` vs `TagEnum.AI_SUGGESTED`).
   - Observed facts (PyPI release dates, pinned versions, AST lines) are never blurred with AI hypotheses.
3. **Red Team: Compatibility Gate Tests (Set A & Set B)**:
   - **Set A (Compatibility Gate)**: Tests the existing observable contract. **Must pass on the old library first** before gating the migrated code. If it fails on the old library, the test is rejected.
   - **Set B (Differential / Edge-Case Tests)**: Probes subtle behavioral shifts, strict error handling, and modern library features.
4. **Blue Team: AST Migration & Self-Healing Repair Loop**:
   - Synthesizes clean drop-in replacement code and standard unified diffs (`difflib.unified_diff`).
   - **Anti-Cheat Guard**: Strictly forbids deleting or bypassing assertions.
   - **Self-Healing Loop**: Ingests test failure tracebacks from Person 1 (Referee) and iteratively produces repaired patches.

---

## 🚀 Quickstart & Demo

You can run the full end-to-end demo immediately (100% offline, zero setup required):

```bash
# Run the complete LinkWatch demonstration
python -m dependency_whisperer.cli demo
```

### CLI Commands

```bash
# 1. Triage a dependency and get top 3 modern replacements with API mappings
python -m dependency_whisperer.cli triage --dep toml --version 0.10.2 --hero LinkWatch/linkwatch/config.py

# 2. Generate Set A & Set B pytest test suite
python -m dependency_whisperer.cli tests --dep appdirs --hero LinkWatch/linkwatch/cache.py --out-dir referee_sandbox

# 3. Generate drop-in code migration patch & unified diff
python -m dependency_whisperer.cli migrate --dep appdirs --hero LinkWatch/linkwatch/cache.py

# 4. Run the full pipeline and output the complete Exit Capsule JSON
python -m dependency_whisperer.cli full-run --dep appdirs --version 1.4.4 --hero LinkWatch/linkwatch/cache.py --out-capsule capsule.json
```

---

## 🧪 Running Unit Tests

The test suite runs independently and validates all schemas, prompt builders, mock engines, and pipeline adapters:

```bash
python -m pytest dependency_whisperer/tests
```

All 10 unit tests run in `< 0.5s` with zero external network dependencies.

---

## 🔌 Team Integration Contract

See [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md) for copy-paste integration snippets for:
- **Person 1 (Referee)**: Sandbox test execution and failure feedback.
- **Person 2 (Detective)**: AST scan ingestion and usage locations.
- **Person 4 (Presenter)**: Markdown Exit Capsule rendering.
