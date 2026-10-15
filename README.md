# Gemma 4 Dependency Exit Capsule

## 1. Problem and Solution Overview

* **The Problem:** Dependency migration is highly risky and often avoided by maintainers because rewriting code across multiple files introduces subtle syntax bugs and merge conflicts. Standard AI tools fail at this because they simply attempt to rewrite entire files via chat, often hallucinating test passes or cheating by modifying the tests themselves.


* **The Solution:** This project is an automated software resilience lab that pairs Gemma 4 with an Inference-Time Search (Monte Carlo Tree Search) and deterministic sandboxed execution. Instead of blindly replacing code, the system calculates the "blast radius" of a bad dependency, slices the code using an Abstract Syntax Tree (AST), and isolates the changes. It then forces the AI into an Asymmetric Adversarial Arena: a "Red Team" AI generates edge-case tests, while a "Blue Team" AI attempts to write the patch. A Python execution harness acts as an absolute referee, running the tests in a sandbox and scoring the AI's patch deterministically. The final output is a verifiable "Dependency Exit Capsule" containing mathematical proof of the safest migration path.



## 2. Setup Instructions

* Ensure you have Python installed on your system.
* Clone the repository and set up the expected folder structure containing `analyzer/`, `ai/`, `engine/`, and `ui/` directories.


* Install the required terminal interface dependencies by running `pip install rich questionary`.


* Obtain a Google AI Studio API key and set it as an environment variable (e.g., `GEMINI_API_KEY`), or install Ollama locally to run the models on your own hardware.



## 3. Usage Instructions

* Start the interactive terminal wizard by executing the main Python script (e.g., `python ui/cli.py` or `python main.py`).


* When prompted by the CLI, select the at-risk dependency you want to replace from the detected list, or type a custom package name.


* The tool will automatically detect the "Hero File" (the file with the highest blast radius); press Enter to confirm this or type a manual override.


* Review the three replacement candidates suggested by the AI and select one to test.


* The system will run the MCTS search and adversarial sandbox, displaying live spinners and branch evaluations.


* Once finished, view the generated `CAPSULE.md` file in your root directory to see the verified execution logs and the Mermaid state diagram.



## 4. Architecture

The architecture is divided into four isolated modules that enforce a strict separation of powers:

* **analyzer/ (AST & Blast Radius):** Performs static code analysis using AST to find all call sites of the deprecated library, computes the blast radius score, and isolates the "Hero File". It also acts as an anti-cheat auditor, scanning the generated patches to ensure the AI did not delete assertions or hardcode literal values.


* **ai/ (Gemma 4 Cognitive Engine):** Manages the AI prompt instructions. It splits Gemma 4 into a Red Team fuzzer (which writes extreme edge-case tests like null payloads) and a Blue Team migrator (which generates unified Git diffs to patch the code).


* **engine/ (Search Loop & Sandbox Runner):** The deterministic brain of the operation. It treats the code migration as a search game, running the AI's patches inside ephemeral subprocesses (like pytest). It calculates a reward score based on clean compilation, passing tests, and execution latency, automatically dropping branches that fail.


* **ui/ (Interactive CLI & Exit Capsule):** Builds the front-end using terminal rendering libraries. It handles the interactive user menus, displays the live AST tree and search progress, and formats the final `exit-capsule.json` and `CAPSULE.md`.



## 5. Dependencies

* `rich` and `questionary`: Required for building the interactive terminal UI, live dashboards, and menus.


* `google-genai` SDK or the standard `openai` Python SDK: Required for communicating with the Gemma 4 API or a local Ollama instance.


* `pytest` (or `npm test`): Required by the execution sandbox to run native test commands in subprocesses.


* `ast` (Python standard library) or `tree-sitter`: Required for parsing code into Abstract Syntax Trees.



## 6. AI Model Details

* **Model Name:** Gemma 4.


* **Model Version:** Includes variants such as the 31B dense flagship, the 26B A4B Mixture-of-Experts, and the E4B/E2B edge-optimized models. (Note: `gemini-2.5-flash` is listed as a potential API fallback in the codebase).


* **Source Access Method:** The model can be accessed via local execution using Ollama or vLLM, through the Google AI Studio / Vertex AI Cloud API, or via Python Transformers.


* **Applicable License:** Released under the Apache 2.0 open-weight license.


* **Role in the Project:** The model is strictly utilized for reasoning and code generation. It acts as a candidate recommender, an adversarial Red Team generating unseen edge-case tests, and a Blue Team generating structured unified Git diffs to replace the old library. The model does not execute code; it only outputs JSON and patches to the Python harness.



## 7. Known Limitations

* **Ecosystem Constraints:** The pipeline's automated sandbox is typically scoped to one specific ecosystem at a time (e.g., Python with `pytest` and `requirements.txt`, or Node.js with `npm test`), meaning the deterministic execution harness must be adapted for different languages.


* **Context Window Boundaries:** While Gemma 4 supports large context windows, dumping entire codebases into the prompt can cause failures; the system relies heavily on the AST analyzer successfully chunking the codebase into specific function boundaries to keep the inference loop fast.


* **Oracle Reliance:** The system's anti-hallucination filter requires the target repository to have a working legacy state. Newly generated tests must first pass against the original codebase to be locked in as ground truth; if the original code is fundamentally broken, the "Oracle Filter" cannot validate new tests.
