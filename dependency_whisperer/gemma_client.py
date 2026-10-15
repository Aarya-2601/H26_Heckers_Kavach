"""
Gemma 4 Client & Provider Abstraction for Person 3 (The AI Whisperer).

Complies with Track 1 (Gemma 4 : Dependency Resilience) requirements:
- Identifies model, version, access method, and terms.
- Supports hosted API (Google AI Studio / Gemini API), local Ollama/vLLM endpoints,
  and a high-fidelity Deterministic Mock Engine so the team can work offline or without API keys.
"""

import json
import os
import re
from typing import Any, Dict, Optional, Type, TypeVar
import requests
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class GemmaModelMetadata(BaseModel):
    """Metadata required by the competition track."""
    model_name: str = "gemma-4-it"
    model_version: str = "4.0.0-preview"
    family: str = "Gemma Open Models"
    access_method: str = "Hosted API (Google AI Studio) / Local Ollama / Deterministic Mock"
    applicable_terms: str = "Google Gemma Terms of Use (https://ai.google.dev/gemma/terms)"


class GemmaClient:
    """
    Unified client for Gemma 4 communication with multi-backend support:
    1. Hosted Google AI Studio / Gemini API (`GEMMA_API_KEY` or `GEMINI_API_KEY`)
    2. Local Ollama / vLLM API (`OLLAMA_HOST` or `GEMMA_LOCAL_URL`)
    3. Deterministic Mock Engine (Offline mode, 100% reliable for team dev & testing)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemma-4-it",
        backend: Optional[str] = None,  # "hosted", "local", "mock", or None for auto-detect
        local_url: Optional[str] = None,
    ):
        self.metadata = GemmaModelMetadata(model_name=model_name)
        self.api_key = api_key or os.environ.get("GEMMA_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.local_url = local_url or os.environ.get("GEMMA_LOCAL_URL") or "http://localhost:11434/v1/chat/completions"

        if backend:
            self.backend = backend
        elif self.api_key:
            self.backend = "hosted"
        elif os.environ.get("USE_LOCAL_GEMMA"):
            self.backend = "local"
        else:
            self.backend = "mock"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text from Gemma backend."""
        if self.backend == "mock":
            return self._generate_mock(prompt)
        elif self.backend == "hosted":
            return self._generate_hosted(prompt, system_prompt)
        elif self.backend == "local":
            return self._generate_local(prompt, system_prompt)
        else:
            return self._generate_mock(prompt)

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str = ""
    ) -> T:
        """Generate text and parse/validate into a Pydantic schema."""
        raw_text = self.generate(prompt, system_prompt)
        cleaned_json = self.extract_json(raw_text)
        try:
            if hasattr(response_model, "model_validate_json"):
                return response_model.model_validate_json(cleaned_json)
            elif hasattr(response_model, "parse_raw"):
                return response_model.parse_raw(cleaned_json)
        except Exception:
            pass

        try:
            data = json.loads(cleaned_json)
            if hasattr(response_model, "model_validate"):
                return response_model.model_validate(data)
            elif hasattr(response_model, "parse_obj"):
                return response_model.parse_obj(data)
            return response_model(**data)
        except Exception as e:
            raise ValueError(
                f"Failed to validate Gemma response into {response_model.__name__}.\n"
                f"Raw response:\n{raw_text}\nCleaned JSON:\n{cleaned_json}\nError: {e}"
            )

    def extract_json(self, text: str) -> str:
        """Strip markdown fences (```json ... ```) and extract pure JSON."""
        text = text.strip()
        json_fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_fence_match:
            return json_fence_match.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()
        return text

    def _generate_hosted(self, prompt: str, system_prompt: str = "") -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.metadata.model_name}:generateContent?key={self.api_key}"
        )
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "{}"
        except Exception as e:
            print(f"[Whisperer Warning] Hosted Gemma API call failed ({e}). Falling back to Deterministic Mock Engine.")
            return self._generate_mock(prompt)

    def _generate_local(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.metadata.model_name,
            "messages": messages,
            "temperature": 0.1,
        }
        try:
            resp = requests.post(self.local_url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[Whisperer Warning] Local Gemma call failed ({e}). Falling back to Deterministic Mock Engine.")
            return self._generate_mock(prompt)

    def _generate_mock(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "triage" in prompt_lower or "recommend replacements" in prompt_lower:
            return self._mock_triage_response(prompt)
        if "set a:" in prompt_lower or "set_a_tests" in prompt_lower or "compatibility gate" in prompt_lower:
            return self._mock_test_plan_response(prompt)
        if "blue team code fixer" in prompt_lower or "migrate a python source file" in prompt_lower:
            return self._mock_migration_code_response(prompt)
        if "self-healing repair" in prompt_lower or "failed unit tests" in prompt_lower:
            return self._mock_repair_response(prompt)
        return json.dumps({"status": "success", "message": "Generic Gemma mock output"})

    def _mock_triage_response(self, prompt: str) -> str:
        dep = "toml"
        if "appdirs" in prompt.lower():
            dep = "appdirs"
        elif "pkg_resources" in prompt.lower():
            dep = "pkg_resources"
        elif "six" in prompt.lower():
            dep = "six"
        elif "chardet" in prompt.lower():
            dep = "chardet"
        elif "requests" in prompt.lower():
            dep = "requests"

        if dep == "toml":
            return json.dumps({
                "target_dependency": "toml",
                "observed_usage_count": 1,
                "triage": {
                    "dependency_name": "toml",
                    "current_version": {"tag": "OBSERVED", "value": "0.10.2", "source": "requirements.txt"},
                    "is_deprecated": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.98, "rationale": "uiri/toml repository has been unmaintained since 2020 and does not comply with TOML v1.0.0 specs."},
                    "is_unmaintained": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.95, "rationale": "Last PyPI release was October 2020."},
                    "known_vulnerabilities": {"tag": "OBSERVED", "value": [], "source": "OSV Database"},
                    "python_compatibility_risk": {"tag": "AI_SUGGESTED", "value": "HIGH", "confidence": 0.90, "rationale": "Python 3.11+ includes native tomllib in standard library, rendering external toml package obsolete."},
                    "risk_level": "HIGH",
                    "risk_summary": "The 'toml' package is abandoned and non-compliant with TOML v1.0. Python 3.11+ provides native 'tomllib' in the standard library."
                },
                "options": [
                    {
                        "library_name": "tomllib",
                        "recommended_version_spec": "standard-library (Python >=3.11)",
                        "ecosystem_health": "Official Python Standard Library module (PEP 680)",
                        "pros": [
                            "Zero external dependencies",
                            "Strict compliance with TOML 1.0.0 specification",
                            "C-optimized parsing performance"
                        ],
                        "cons": [
                            "Read-only (does not support writing/dumping TOML)",
                            "Requires Python >=3.11 or 'tomli' fallback for Python 3.10"
                        ],
                        "migration_difficulty": "TRIVIAL",
                        "breaking_changes": [
                            "Requires binary mode 'rb' when reading from file pointers",
                            "No dump/dumps function"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "toml.load(path)",
                                "new_symbol": "tomllib.loads(Path(path).read_text(encoding='utf-8'))",
                                "transformation_type": "signature_change",
                                "notes": "tomllib.load requires binary file pointer, loads handles text"
                            }
                        ]
                    },
                    {
                        "library_name": "tomli",
                        "recommended_version_spec": ">=2.0.1",
                        "ecosystem_health": "Very active, upstream source of Python 3.11 tomllib",
                        "pros": [
                            "Drop-in identical behavior to tomllib",
                            "Compatible across Python 3.8 - 3.13"
                        ],
                        "cons": [
                            "Read-only, requires third-party dependency for Python <3.11"
                        ],
                        "migration_difficulty": "TRIVIAL",
                        "breaking_changes": [
                            "Requires binary file stream for load()"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "toml.load(path)",
                                "new_symbol": "tomli.load(open(path, 'rb'))",
                                "transformation_type": "signature_change",
                                "notes": "Binary stream required"
                            }
                        ]
                    },
                    {
                        "library_name": "tomlkit",
                        "recommended_version_spec": ">=0.13.2",
                        "ecosystem_health": "Actively maintained by Poetry team",
                        "pros": [
                            "Style-preserving TOML reader and writer",
                            "Full roundtrip formatting support"
                        ],
                        "cons": [
                            "Slightly heavier memory and CPU footprint"
                        ],
                        "migration_difficulty": "LOW",
                        "breaking_changes": [
                            "Returns TOMLKit container types rather than raw dict"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "toml.load(path)",
                                "new_symbol": "tomlkit.parse(Path(path).read_text())",
                                "transformation_type": "direct_rename",
                                "notes": "Reads string directly"
                            }
                        ]
                    }
                ],
                "recommended_choice": "tomllib"
            })

        elif dep == "appdirs":
            return json.dumps({
                "target_dependency": "appdirs",
                "observed_usage_count": 1,
                "triage": {
                    "dependency_name": "appdirs",
                    "current_version": {"tag": "OBSERVED", "value": "1.4.4", "source": "requirements.txt"},
                    "is_deprecated": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.99, "rationale": "Official appdirs repo has been archived/abandoned since 2020."},
                    "is_unmaintained": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.99, "rationale": "No releases since May 2020."},
                    "known_vulnerabilities": {"tag": "OBSERVED", "value": [], "source": "OSV Database"},
                    "python_compatibility_risk": {"tag": "AI_SUGGESTED", "value": "HIGH", "confidence": 0.95, "rationale": "Modern package managers (pip, virtualenv) migrated entirely to platformdirs."},
                    "risk_level": "CRITICAL",
                    "risk_summary": "'appdirs' has been officially abandoned and replaced across the Python ecosystem by 'platformdirs'."
                },
                "options": [
                    {
                        "library_name": "platformdirs",
                        "recommended_version_spec": ">=4.0.0",
                        "ecosystem_health": "Active, 100M+ monthly downloads, standard community successor",
                        "pros": [
                            "100% API-compatible successor to appdirs",
                            "Supports modern OS specifications (XDG base dir, macOS sandboxing, Windows AppData)",
                            "Active maintenance with Python 3.12/3.13 support"
                        ],
                        "cons": [
                            "Requires minor import rename"
                        ],
                        "migration_difficulty": "TRIVIAL",
                        "breaking_changes": [
                            "None; user_cache_dir signature and behavior are identical"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "from appdirs import user_cache_dir",
                                "new_symbol": "from platformdirs import user_cache_dir",
                                "transformation_type": "direct_rename",
                                "notes": "Direct drop-in replacement"
                            }
                        ]
                    },
                    {
                        "library_name": "pathlib.Path.home",
                        "recommended_version_spec": "standard-library",
                        "ecosystem_health": "Python standard library",
                        "pros": [
                            "Zero external dependencies",
                            "Native path object"
                        ],
                        "cons": [
                            "Requires manual OS-conditional branching for ~/.cache vs ~/Library/Caches vs AppData"
                        ],
                        "migration_difficulty": "MEDIUM",
                        "breaking_changes": [
                            "Must construct platform-specific directory structure manually"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "user_cache_dir('linkwatch')",
                                "new_symbol": "Path.home() / '.cache' / 'linkwatch'",
                                "transformation_type": "structural_rewrite",
                                "notes": "Cross-platform requires os.name checks"
                            }
                        ]
                    },
                    {
                        "library_name": "xdg-base-dirs",
                        "recommended_version_spec": ">=6.0.0",
                        "ecosystem_health": "Actively maintained",
                        "pros": [
                            "Strict XDG compliance",
                            "Lightweight"
                        ],
                        "cons": [
                            "Linux/Unix focused, weaker Windows AppData mapping"
                        ],
                        "migration_difficulty": "MEDIUM",
                        "breaking_changes": [
                            "Does not provide direct user_cache_dir(appname) signature"
                        ],
                        "api_mappings": [
                            {
                                "old_symbol": "user_cache_dir('linkwatch')",
                                "new_symbol": "xdg_cache_home() / 'linkwatch'",
                                "transformation_type": "signature_change",
                                "notes": "Requires path joining"
                            }
                        ]
                    }
                ],
                "recommended_choice": "platformdirs"
            })

        return json.dumps({
            "target_dependency": dep,
            "observed_usage_count": 1,
            "triage": {
                "dependency_name": dep,
                "current_version": {"tag": "OBSERVED", "value": "1.0.0", "source": "requirements.txt"},
                "is_deprecated": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.85, "rationale": "Package shows signs of aging or maintenance lag."},
                "is_unmaintained": {"tag": "AI_SUGGESTED", "value": True, "confidence": 0.80, "rationale": "Infrequent releases and open issues."},
                "known_vulnerabilities": {"tag": "OBSERVED", "value": [], "source": "OSV Database"},
                "python_compatibility_risk": {"tag": "AI_SUGGESTED", "value": "MEDIUM", "confidence": 0.85, "rationale": "Potential deprecation warnings on newer Python runtimes."},
                "risk_level": "MEDIUM",
                "risk_summary": f"Target package '{dep}' requires modern replacement to ensure resilience."
            },
            "options": [
                {
                    "library_name": f"modern-{dep}",
                    "recommended_version_spec": ">=2.0.0",
                    "ecosystem_health": "Active",
                    "pros": ["Modern API", "Full test coverage"],
                    "cons": ["Minor syntax adjustments"],
                    "migration_difficulty": "LOW",
                    "breaking_changes": ["Updated import path"],
                    "api_mappings": [
                        {
                            "old_symbol": f"{dep}.call()",
                            "new_symbol": f"modern_{dep}.call()",
                            "transformation_type": "direct_rename",
                            "notes": "Direct drop-in"
                        }
                    ]
                }
            ],
            "recommended_choice": f"modern-{dep}"
        })

    def _mock_test_plan_response(self, prompt: str) -> str:
        dep = "appdirs" if "appdirs" in prompt.lower() else "toml"
        replacement = "platformdirs" if dep == "appdirs" else "tomllib"

        if dep == "appdirs":
            pytest_content = (
                "import os\n"
                "from linkwatch.cache import cache_dir, cache_file, save_results, load_results\n\n"
                "# SET A: Compatibility Gate Tests\n"
                "def test_set_a_cache_dir_returns_valid_string_path(monkeypatch, tmp_path):\n"
                "    monkeypatch.setenv('LINKWATCH_CACHE_DIR', str(tmp_path / 'custom_cache'))\n"
                "    cdir = cache_dir()\n"
                "    assert isinstance(cdir, str)\n"
                "    assert os.path.isdir(cdir)\n"
                "    assert cdir == str(tmp_path / 'custom_cache')\n\n"
                "def test_set_a_roundtrip_save_and_load(tmp_path, monkeypatch):\n"
                "    monkeypatch.setenv('LINKWATCH_CACHE_DIR', str(tmp_path))\n"
                "    data = [{'name': 'Test', 'url': 'https://example.com', 'up': True}]\n"
                "    saved_path = save_results(data)\n"
                "    assert os.path.exists(saved_path)\n"
                "    loaded = load_results()\n"
                "    assert loaded == data\n\n"
                "# SET B: Differential & Edge-Case Tests\n"
                "def test_set_b_default_cache_dir_resolution_without_env(monkeypatch):\n"
                "    monkeypatch.delenv('LINKWATCH_CACHE_DIR', raising=False)\n"
                "    cdir = cache_dir()\n"
                "    assert 'linkwatch' in cdir.lower()\n"
                "    assert os.path.exists(cdir)\n\n"
                "def test_set_b_cache_file_path_conformance():\n"
                "    cfile = cache_file()\n"
                "    assert cfile.endswith('results.json')\n"
            )
            return json.dumps({
                "target_dependency": "appdirs",
                "replacement_library": "platformdirs",
                "set_a_tests": [
                    {
                        "test_id": "SET_A_01",
                        "name": "test_set_a_cache_dir_returns_valid_string_path",
                        "category": "SET_A_COMPATIBILITY_GATE",
                        "description": "Verifies cache_dir() contract: returns created valid directory path string.",
                        "test_code": "def test_set_a_cache_dir_returns_valid_string_path(monkeypatch, tmp_path):\n    ...",
                        "expected_behavior": "Must pass on both old and new implementations",
                        "validity_gate_passed": True
                    }
                ],
                "set_b_tests": [
                    {
                        "test_id": "SET_B_01",
                        "name": "test_set_b_default_cache_dir_resolution_without_env",
                        "category": "SET_B_DIFFERENTIAL",
                        "description": "Probes default directory resolution when LINKWATCH_CACHE_DIR is unset.",
                        "test_code": "def test_set_b_default_cache_dir_resolution_without_env(monkeypatch):\n    ...",
                        "expected_behavior": "Probes modern platformdirs directory mapping across OS standards",
                        "validity_gate_passed": True
                    }
                ],
                "full_pytest_file_content": pytest_content
            })
        else:
            pytest_content = (
                "from linkwatch.config import load_settings, Settings\n\n"
                "def test_set_a_load_settings_contract(tmp_path):\n"
                "    p = tmp_path / 'sites.toml'\n"
                "    p.write_text('title = \"Test\"\\noutput = \"out.html\"\\n', encoding='utf-8')\n"
                "    s = load_settings(str(p))\n"
                "    assert isinstance(s, Settings)\n"
            )
            return json.dumps({
                "target_dependency": "toml",
                "replacement_library": "tomllib",
                "set_a_tests": [
                    {
                        "test_id": "SET_A_01",
                        "name": "test_set_a_load_settings_contract",
                        "category": "SET_A_COMPATIBILITY_GATE",
                        "description": "Verifies load_settings() loads standard TOML file into Settings model accurately.",
                        "test_code": "def test_set_a_load_settings_contract(tmp_path):\n    pass",
                        "expected_behavior": "Must pass on both old and new implementations",
                        "validity_gate_passed": True
                    }
                ],
                "set_b_tests": [],
                "full_pytest_file_content": pytest_content
            })

    def _mock_migration_code_response(self, prompt: str) -> str:
        if "appdirs" in prompt.lower() or "cache.py" in prompt.lower():
            return (
                "import json\nimport os\n\nfrom platformdirs import user_cache_dir\n\n"
                "RESULTS_FILE = \"results.json\"\n\n"
                "def cache_dir():\n"
                "    path = os.environ.get(\"LINKWATCH_CACHE_DIR\") or user_cache_dir(\"linkwatch\")\n"
                "    os.makedirs(path, exist_ok=True)\n"
                "    return path\n\n"
                "def cache_file():\n"
                "    return os.path.join(cache_dir(), RESULTS_FILE)\n\n"
                "def save_results(results):\n"
                "    path = cache_file()\n"
                "    with open(path, \"w\", encoding=\"utf-8\") as fh:\n"
                "        json.dump(results, fh, indent=2)\n"
                "    return path\n\n"
                "def load_results():\n"
                "    path = cache_file()\n"
                "    if not os.path.exists(path):\n"
                "        return []\n"
                "    with open(path, encoding=\"utf-8\") as fh:\n"
                "        return json.load(fh)\n"
            )
        return (
            "from typing import List\n"
            "try:\n    import tomllib\nexcept ModuleNotFoundError:\n    import tomli as tomllib\n"
            "from pydantic import BaseModel\n\n"
            "class Settings(BaseModel):\n    title: str = 'linkwatch'\n\n"
            "def load_settings(path='sites.toml'):\n"
            "    with open(path, 'rb') as fh:\n"
            "        data = tomllib.load(fh)\n"
            "    return Settings(**data)\n"
        )

    def _mock_repair_response(self, prompt: str) -> str:
        return json.dumps({
            "success": True,
            "root_cause_diagnosis": "TypeError encountered because tomllib.load requires a binary file stream ('rb') rather than text mode or string path.",
            "changes_applied": [
                "Updated file open mode to 'rb' inside load_settings",
                "Ensured stream is safely closed with context manager"
            ],
            "confidence_score": 0.98,
            "repaired_code": (
                "from typing import List\ntry:\n    import tomllib\nexcept ModuleNotFoundError:\n    import tomli as tomllib\n"
                "from pydantic import BaseModel\n\n"
                "class Settings(BaseModel):\n    title: str = 'linkwatch'\n\n"
                "def load_settings(path='sites.toml'):\n"
                "    with open(path, 'rb') as fh:\n"
                "        data = tomllib.load(fh)\n"
                "    return Settings(**data)\n"
            )
        })
