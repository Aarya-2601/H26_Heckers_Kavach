# 🤝 Team Integration Guide

This guide allows **Person 1 (Referee)**, **Person 2 (Detective)**, and **Person 4 (Presenter)** to connect with **Person 3 (The AI Whisperer)** seamlessly without merge conflicts.

You can either:
1. **Import directly in Python** (`from dependency_whisperer import ...`)
2. **Use JSON files or CLI commands** to pass data between each other.

---

## 🔍 1. For Person 2: The Detective (Code Scanner)

### What to pass to Person 3:
When you finish scanning the repository and finding which dependencies are imported and where, pass the data as a dictionary or write it to a JSON file.

### Python Integration Example:
```python
from dependency_whisperer.adapters import TeamBridge
from dependency_whisperer import DependencyWhisperer

bridge = TeamBridge(whisperer=DependencyWhisperer())

# Pass your scan results (or the path to your scan output JSON):
detective_output = {
    "dependency": "appdirs",
    "version": "1.4.4",
    "hero_file": "LinkWatch/linkwatch/cache.py",
    "usage_locations": [
        {"file": "LinkWatch/linkwatch/cache.py", "line": 4, "snippet": "from appdirs import user_cache_dir"}
    ]
}

# Ingest and start triage:
parsed_data = bridge.ingest_detective_data(detective_output)
triage_result = bridge.whisperer.triage_and_suggest_replacements(
    dependency_name=parsed_data["dependency_name"],
    detected_version=parsed_data["detected_version"],
    hero_file=parsed_data["hero_file"],
    hero_code=parsed_data["hero_code"],
)

print("Top 3 Replacement Options:", [opt.library_name for opt in triage_result.options])
print("Recommended Choice:", triage_result.recommended_choice)
```

---

## ⚖️ 2. For Person 1: The Referee (Execution & Scoring)

### What Person 3 gives you:
Person 3 automatically generates:
1. A standalone **`test_<dep>_migration.py`** containing **Set A** (compatibility gate) and **Set B** (differential) tests.
2. The migrated Python file candidate.
3. A unified `.patch` file.

### Step 1: Receiving the Test Files
```python
from dependency_whisperer.adapters import TeamBridge
from dependency_whisperer import DependencyWhisperer

whisperer = DependencyWhisperer()
bridge = TeamBridge(whisperer=whisperer)

# Generate test suite and code patch
test_suite = whisperer.generate_compatibility_suite(
    dependency_name="appdirs",
    replacement_library="platformdirs",
    hero_file="LinkWatch/linkwatch/cache.py",
    hero_code=open("LinkWatch/linkwatch/cache.py").read()
)
patch = whisperer.synthesize_migration(
    target_file="LinkWatch/linkwatch/cache.py",
    original_code=open("LinkWatch/linkwatch/cache.py").read(),
    target_dependency="appdirs",
    replacement_library="platformdirs",
)

# Export directly into your sandbox folder:
exported_files = bridge.export_referee_payload(test_suite, patch, output_dir="referee_sandbox")
print("Run pytest on:", exported_files["pytest_file"])
print("Test the migrated code at:", exported_files["migrated_file"])
```

### Step 2: The Self-Healing Repair Loop (If Tests Fail)
If your test run fails (e.g., pytest exits with an error or traceback), pass the error logs back to Person 3 to heal the code:

```python
failure_report = {
    "target_file": "LinkWatch/linkwatch/cache.py",
    "target_dependency": "appdirs",
    "replacement_library": "platformdirs",
    "current_migrated_code": open(exported_files["migrated_file"]).read(),
    "test_stdout": stdout_text,
    "test_stderr": stderr_traceback,
    "attempt_number": 1
}

# Person 3 will diagnose the error and return the repaired code!
repaired_result = bridge.ingest_referee_failure(failure_report)
print("Diagnosis:", repaired_result.root_cause_diagnosis)
print("Changes Applied:", repaired_result.changes_applied)

# Write repaired code and re-test:
with open(exported_files["migrated_file"], "w", encoding="utf-8") as fh:
    fh.write(repaired_result.repaired_code)
```

---

## 🎨 3. For Person 4: The Presenter (UI / CLI & Report)

### What Person 3 gives you:
Person 3 produces the **`ExitCapsulePayload`**, which has strict separation between **`[OBSERVED]`** facts and **`[AI-SUGGESTED]`** recommendations.

### Python Integration Example:
```python
from dependency_whisperer.adapters import TeamBridge

bridge = TeamBridge()

# Either load from json or get directly from whisperer:
# capsule = whisperer.build_exit_capsule_payload(...)
capsule_dict = bridge.export_presenter_capsule(capsule, output_json_path="exit_capsule.json")

# Grounded separation ready for your Markdown or Rich tables:
print("OBSERVED FACTS:")
print("- Pinned Version:", capsule_dict["observed_evidence"]["detected_version"])
print("- Execution Evidence:", capsule_dict["observed_evidence"]["execution_evidence"])

print("AI-SUGGESTED RECOMMENDATIONS:")
print("- Risk Assessment:", capsule_dict["ai_recommendations"]["triage_summary"])
print("- Primary Replacement:", capsule_dict["ai_recommendations"]["recommended_replacement"]["library_name"])
print("- Confidence Score:", capsule_dict["ai_recommendations"]["confidence_score"])
```

---

## 💡 Running Offline / Without API Keys
Every module defaults to the **Deterministic Mock Engine** (`backend="mock"`).  
If you have a Google AI Studio API key, set `export GEMMA_API_KEY="your-key"` or pass `--backend hosted`.  
Otherwise, the mock engine provides realistic outputs for `toml`, `appdirs`, `pkg_resources`, and other dependencies so you can test end-to-end anytime.
