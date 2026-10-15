# Gemma 4 Dependency Exit Capsule Engine

This repository implements an automated software resilience lab designed to migrate deprecated dependencies using Gemma 4. Rather than acting as a standard LLM chat wrapper, this system utilizes an Inference-Time Search (MCTS) architecture, an Asymmetric Adversarial Arena (Red/Blue teams), and deterministic sandboxed execution to empirically prove the safest migration path.

## Core Architecture & Innovations

* **AST Blast Radius & Hero Files:** Uses static analysis to calculate a blast radius score and pinpoint the "Hero File" (the file with the highest dependency coupling). This isolates the exact bytes being mutated and prevents context window fragmentation.


* **Adversarial Testing (Red vs. Blue):** Employs Gemma 4 in two distinct roles. The Red Team acts as a fuzzer generating extreme edge-case tests (null payloads, boundary limits), while the Blue Team generates unified diff patches for the migration.


* **The Oracle & Anti-Tamper Sandbox:** Generated tests are first run against the legacy codebase; if they pass, they are locked into an immutable vault. A deterministic auditor verifies the Git diff to ensure the AI does not cheat by deleting assertions or hardcoding literal values.


* **Deterministic Reward Engine:** A Python harness scores proposed migration patches based on clean compilation, passing sandboxed tests, latency, and code bloat. This forces the search tree to dynamically abandon inferior patches and auto-heal errors without fine-tuning weights.


* **The Exit Capsule:** Generates a verifiable `CAPSULE.md` and `exit-capsule.json` featuring a Mermaid.js state exploration graph, strictly separating raw deterministic test telemetry from AI reasoning.



## Repository Structure

* `analyzer/`: Static code analysis. Scans for target packages, extracts call sites, computes the blast radius, and runs the anti-cheat AST guard.


* `ai/`: Gemma 4 cognitive engine. Handles prompts for replacement candidate recommendations, Red Team fuzzer tests, and Blue Team migration diffs.


* `engine/`: The execution backend. Manages the MCTS search state machine, ephemeral subprocess test sandboxing, and calculates the reward score.


* `ui/`: Interactive front-end. Powers the terminal wizard, renders the AST tree visualizer, and builds the final Exit Capsule deliverable.



## 6-Hour Plan of Action

**Phase 1: Foundation & Contract Locking (0:00 - 0:20)**

* Initialize repository and install `rich` and `questionary` dependencies.


* Commit the three frozen JSON mock schemas (`ast_output.json`, `gemma_output.json`, `run_result.json`) to the `contracts/` directory to enable simultaneous development.



**Phase 2: Isolated Development (0:20 - 3:30)**

* **Person 1 (Engine):** Build `sandbox.py` to capture raw exit codes/stderr via subprocess, and construct the `rewards.py` heuristic calculator.


* **Person 2 (Analyzer):** Build `ast_scanner.py` to walk AST nodes for call sites, and `blast_radius.py` to calculate file hit counts.


* **Person 3 (AI):** Build `gemma_client.py` and configure the Google GenAI SDK to return structured JSON for candidate options, adversarial tests, and patches.


* **Person 4 (UI):** Build `cli.py` to handle user selection menus and the interactive live dashboard.



**Phase 3: Pairwise Integration (3:30 - 4:45)**

* **Pair A (Person 2 + 4):** Hook the AST parser and Hero File selector into the interactive CLI menus.


* **Pair B (Person 1 + 3):** Connect Gemma 4 outputs directly into the MCTS search loop and isolated sandbox runner.



**Phase 4: Master Integration (4:45 - 5:30)**

* Create `main.py` entry point.


* Wire the UI to invoke the search loop with user-selected parameters and run the entire pipeline against a target repository.



**Phase 5: Polish & Demo Prep (5:30 - 6:00)**

* Generate the final `CAPSULE.md`.


* Review AST metrics, telemetry separation, and Mermaid graphs.


* Execute the live demo script end-to-end to confirm terminal aesthetics and slide timings.
