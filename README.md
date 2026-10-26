# Gemma 4 Dependency Exit Capsule

## 1. Problem and Solution Overview

* **The Problem:** Dependency migration is highly risky and often avoided by maintainers because rewriting code across multiple files introduces subtle syntax bugs, API regressions, and merge conflicts. Standard AI tools fail at this because they simply attempt to rewrite entire files via chat, often hallucinating test passes or cheating by modifying the tests themselves.


* **The Solution:** This project is an automated software resilience lab that pairs Gemma 4 with an Inference-Time Search (Monte Carlo Tree Search) and deterministic sandboxed execution. Instead of blindly replacing code, the system calculates the "blast radius" of a bad dependency, slices the code using an Abstract Syntax Tree (AST), and isolates the changes. It then forces the AI into an Asymmetric Adversarial Arena: a "Red Team" AI generates edge-case tests, while a "Blue Team" AI attempts to write the patch. A Python execution harness acts as an absolute referee, running the tests in an ephemeral sandbox and scoring the AI's patch deterministically. The final output is a verifiable "Dependency Exit Capsule" containing mathematical proof of the safest migration path.



## 2. Setup Instructions

* Ensure you have Python 3.10+ installed on your system.
* Install project dependencies:
  ```bash
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  ```
* Optional API Key: To use hosted Gemma 4 or Gemini models, set your API key:
  ```bash
  export GEMINI_API_KEY="your-api-key"   # Linux/macOS
  $env:GEMINI_API_KEY="your-api-key"    # Windows PowerShell
  ```
  *(If no key is provided, the tool automatically defaults to high-fidelity mock inference mode for offline demonstration).*



## 3. Usage & CLI Workflow

You can run the engine via the CLI orchestrator or through the interactive Web Dashboard:

### 3.1 Interactive CLI Wizard
```bash
python main.py
```
* **Step 1:** The CLI displays the repository tree and scans package manifests (`requirements.txt`, `pyproject.toml`) and AST call sites.
* **Step 2:** Select the dependency you wish to migrate from the interactive menu. Dependencies already migrated in previous runs will be prominently labeled with `[ALREADY MIGRATED ✓]`.
* **Step 3:** The tool identifies the **Hero File** (highest blast radius) and displays call site traces.
* **Step 4:** Review the candidate replacements suggested by Gemma 4 and confirm maintainer directives.
* **Step 5:** Watch the Red Team fuzzer synthesize multi-dimensional edge cases, followed by the MCTS Auto-Heal search in an ephemeral sandbox.
* **Step 6 (On-Disk Application):** When tests pass, the wizard asks:
  ```text
  Apply verified patch for '<package>' directly to '<repo>' on disk? [y/N]: y
  ```
  Answering **Yes** applies the patch to your working tree, updates your manifests, logs the change, and runs a ground-truth test suite directly on disk.

### 3.2 Non-Interactive Single-Shot Migration with `--apply`
To automate the migration and immediately apply verified fixes directly to your repository:
```bash
python main.py --repo dataset/LinkWatch
```

### 3.3 Multi-Dependency Sequential Migrations
When migrating multiple dependencies across a repository:
1. Migrate the first dependency:
   ```bash
   python main.py --repo dataset/LinkWatch
   ```
2. The migration is applied to disk and recorded in `.kavach_migrations.json`.
3. When running the next migration:
   ```bash
   python main.py --repo dataset/LinkWatch --package toml --apply
   ```
   The engine recognizes that `appdirs` is already resolved and focuses on `toml`.

### 3.4 Interactive Web Dashboard
To launch the real-time visual web application:
```bash
python run_web.py --port 5000
```
Open `http://localhost:5000` in your browser to inspect repositories, view blast radius AST graphs, trigger migrations, and inspect execution telemetry.



## 4. Architecture & Modular Roles

The architecture is divided into isolated modules that enforce a strict separation of powers:

* **analyzer/ (AST & Blast Radius — Person 2 Detective):**
  Performs static code analysis using AST to trace all call sites of the target library, computes blast radius scores, and isolates the "Hero File". Scans generated patches to ensure no test assertions were deleted or weakened.

* **dependency_whisperer/ (Gemma 4 Cognitive Engine — Person 3 AI Whisperer):**
  Orchestrates LLM prompts with strict Pydantic contract validation. Operates the Red Team adversarial fuzzer (synthesizing Set A baseline gates and Set B differential edge cases) and Blue Team migration code generator with self-healing auto-repair.

* **engine/ (Search Loop & Ephemeral Sandbox — Person 1 Referee):**
  The deterministic referee. Copies the target repository into an isolated, ephemeral scratch directory (`tempfile.TemporaryDirectory()`). Runs candidate patches against the test runner (`pytest`), applies anti-tampering checks, computes mathematical reward scores, and drops invalid branches.

* **src/ (Presenter & Patch Applier — Person 4 Presenter):**
  Renders the Rich terminal UI, interactive Questionary menus, real-time audit checklist, decision DAG, and delivers `CAPSULE.md` and `capsule_decision_tree.png`. Handles safe on-disk patch application ([`src/patch_applier.py`](file:///c:/Users/Keya/Desktop/H26_Heckers_Kavach/src/patch_applier.py)) and tracks migration history in `.kavach_migrations.json`.



## 5. Artifacts & Deliverables

Every migration run generates verifiable, audit-ready deliverables:
* **`CAPSULE.md`:** A comprehensive markdown deliverable containing executive summaries, AST blast radius metrics, candidate comparison tables, complete unified git diffs, and an interactive Mermaid state diagram.
* **`capsule_decision_tree.png`:** A graphical decision tree visualizing explored nodes, test scores, and winning paths.
* **`contracts/ast_output.json`:** Ground-truth call-site AST coordinates.
* **`contracts/gemma_output.json`:** Red Team edge-case test suite and compatibility gates.
* **`contracts/run_result.json`:** Comprehensive execution telemetry, sandbox execution times, and exit codes.
* **`.kavach_migrations.json`:** Persistent history on the target repository logging verified on-disk migrations.



## 6. AI Model Details

* **Model Family:** Gemma 4 / Gemma 2.
* **Model Versions Supported:** 31B dense flagship, 26B A4B Mixture-of-Experts, and Gemini 2.5 Flash / Flash-Lite API fallbacks.
* **Backend Options:**
  - `hosted`: Connects to Google AI Studio via `GEMINI_API_KEY`.
  - `local`: Connects to local Ollama / vLLM runtime.
  - `mock`: Built-in zero-dependency deterministic simulation for offline evaluation and CI testing.
* **Role in the Project:** Strict reasoning and patch generation. The model outputs structured JSON and unified diffs; it never directly executes code or modifies production systems.



## 7. Safety, Anti-Cheating & Known Limitations

* **Anti-Cheat Tampering Detection:** The engine automatically rejects patches that touch test files (`tests/`), modify test assertions, or inject unvetted global monkey-patches.
* **Ephemeral First, Disk Second:** Patches are **never** applied directly to your source files until they have passed sandboxed test execution with 100% pass rates and received maintainer confirmation (`--apply`).
* **Oracle Reliance:** The system's anti-hallucination filter validates that pre-existing contracts pass before scoring new edge-case tests.
