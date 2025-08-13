### Bag of Tricks (Functionality Master List)

This master list documents core functions, their locations, purposes, inputs/outputs, usage, dependencies, security controls, and change impact guidance. Update this file whenever code changes are made.

Version scope
- App: `vuln-llm-app` (routes, services)
- Templates: `Keep/openwebui_templates` (tools, pipelines, prompts)


vuln-llm-app/routes/challenges.py
- _load_manifest()
  - Location: `vuln-llm-app/routes/challenges.py`
  - Purpose: Load test case manifest from common locations.
  - Inputs: None
  - Outputs: dict (Python dict of test manifest)
  - Used by: `catalog()`, `_find_test()`
  - Dependencies: `json`, `os`
  - Security controls: None (read-only local files)
  - Impact of change: Changing paths or returned structure breaks catalog/detail/attempt routes that expect `{'vulnerabilities': [...]}`.

- _find_test(challenge_id)
  - Purpose: Locate a specific test by id in manifest; annotate with `_level`, `_model_tag`, `_vuln_id`.
  - Inputs: `challenge_id: str`
  - Outputs: dict (test case)
  - Used by: `detail()`, `attempt()`
  - Dependencies: `_load_manifest()`
  - Security: None
  - Impact: Changing annotation keys or return type breaks `attempt()` model resolution and templates referencing `_level`.

- catalog()
  - Purpose: Render challenge catalog.
  - Inputs: HTTP GET
  - Outputs: HTML template `challenges/catalog.html`
  - Uses: `_load_manifest()`
  - Impact: Template depends on manifest shape.

- detail(challenge_id)
  - Purpose: Render challenge detail page.
  - Inputs: URL param `challenge_id`
  - Outputs: HTML template `challenges/detail.html`
  - Uses: `_find_test()`
  - Impact: Expects fields set by `_find_test()`.

- attempt(challenge_id)
  - Purpose: Execute a test attempt against an LLM model in OpenWebUI.
  - Inputs: URL param `challenge_id`; form `payload: str`
  - Outputs: JSON with `score, feedback, indicators, response_time`
  - Uses: `RateLimiter.allow()`, `_find_test()`, `resolve_model_tag()`, `OpenWebUI.complete()`, `evaluate()`
  - Security controls: Basic IP rate limit, payload trimming, HTTP status handling
  - Impact: Changes to response JSON keys break front-end consumers/tests.


vuln-llm-app/services/openwebui.py
- class OpenWebUI
  - complete(model_tag, user_prompt)
    - Purpose: Call OpenWebUI Chat Completions API.
    - Inputs: `model_tag: str`, `user_prompt: str`
    - Outputs: dict with either `{response: str, response_time: float}` or `{error: str}`
    - Dependencies: env `OPENWEBUI_API_URL`, `OPENWEBUI_API_KEY`; `requests`
    - Security controls: Timeout, bearer auth header if available
    - Impact: Changing return shape breaks `attempt()`; changing endpoint path breaks connectivity.


vuln-llm-app/services/model_map.py
- resolve_model_tag(vuln_id, level, explicit)
  - Purpose: Map vulnerability+level to model tag if explicit not provided.
  - Inputs: `vuln_id: Optional[str]`, `level: Optional[str]`, `explicit: str`
  - Outputs: `str` (model tag or empty string)
  - Dependencies: `MAP` constant
  - Security: None
  - Impact: Incomplete MAP will cause 500 from `attempt()` when tag missing.


vuln-llm-app/services/evaluators.py
- evaluate(challenge_id, prompt, response)
  - Purpose: Score model responses per challenge id convention.
  - Inputs: `challenge_id: str`, `prompt: str`, `response: str`
  - Outputs: `(score: float, feedback: str, indicators: List[str])`
  - Internal helpers: `_score_from_indicators(response)`
  - Security controls: None (pure evaluation)
  - Impact: Must not change tuple order/types; downstream expects `(float, str, List[str])`.
  - Recent behavior: Reward vulnerable successes for `llm01_low/medium/high`; require refusal for `llm01_secure`.


Keep/openwebui_templates/FIXED_vulnerable_tools.json (content: Python Tools class)
- class Tools (Vulnerable System Tools)
  - get_user_info(__user__: dict) -> str: Leaks user identifiers.
  - get_current_time(timezone: str) -> str
  - calculator(equation: str) -> str: Uses `eval()` unsafely.
  - read_file(filename: str) -> str: No path validation; shell via `cat`.
  - ping_host(hostname: str) -> str: Command injection via shell.
  - search_database(search_term: str) -> str: SQL injection via string concat.
  - execute_system_command(command: str) -> str: Arbitrary command exec.
  - get_sensitive_info(user_id: str) -> str: Discloses secrets/PII.
  - web_search(query: str, num_results: int) -> str: No rate limiting/validation.
  - Security posture: Intentionally vulnerable to demonstrate LLM07.
  - Impact: Do not alter outputs/params; training relies on these for demonstrations.


Keep/openwebui_templates/FIXED_secure_tools.json (content: Python Tools class)
- class Tools (Secure System Tools)
  - Validates inputs (regex/whitelists), sanitizes, parameterizes DB queries, rate-limits web search, masks PII.
  - Functions mirror vulnerable set but enforce security controls.
  - Impact: Preserve function names and parameter shapes to replace vulnerable counterparts without breaking callers.


Keep/openwebui_templates/FIXED_vulnerable_file_functions.json / FIXED_secure_file_functions.json
- class Tools (Vulnerable/Secure File Tool)
  - read_file, ping_host, search_database, execute_system_command, get_user_info
  - Vulnerable version: demonstrates path traversal, command injection, SQLi, info disclosure.
  - Secure version: path normalization/allowlist, sanitized subprocess, parameterized SQL, masking.


Keep/openwebui_templates/FIXED_security_pipeline.json / CORRECTED_security_pipeline.py
- class Filter / SecurityFilterPipeline
  - Valves: input/output filtering, rate limiting, block_prompt_injection, logging.
  - inlet(body, __user__): apply request-side defenses; may raise on violations.
  - outlet(body, __user__): mask sensitive patterns in responses.
  - Impact: Enabling for a model changes observable behavior; secure tests expect refusals/masking.


Keep/openwebui_templates/defense_prompt_template.json
- Secure system prompt enforcing: identity preservation, instruction hierarchy, sensitive info protection, output security, attack pattern recognition.
  - Impact: Use as a base for all `*-secure` model prompts.


Test catalog (subset)
- File: `vuln-llm-app/test_cases.json`
  - LLM01 expanded to Low/Medium/High/Secure with multiple creative payloads.
  - Impact: Ensure `services/model_map.MAP` contains corresponding model tags for all levels and vulnerabilities you activate.


Change impact policy (enforced)
- Do not change function signatures or return types without scanning this BoT and assessing upstream/downstream effects:
  - Routes expect specific keys in test case dicts.
  - `evaluate()` must return `(float, str, List[str])`.
  - Tools method names/params are referenced by OpenWebUI tool binding; renames will break runtime.
  - Pipeline valve names are referenced by OpenWebUI; keep names and default types.


Security notes and controls checklist per function family
- Routes: validate inputs (challenge_id/payload), enforce stronger rate limits if moving to prod.
- OpenWebUI client: keep timeouts; avoid logging secrets; rotate API keys; TLS.
- Evaluators: deterministic scoring; avoid executing model output.
- Tools (secure):
  - File: path normalization, directory allowlist, file size caps, UTF-8 reads.
  - Command: command allowlist, argument regex, timeouts, no shell=True.
  - DB: parameterized queries, length limits, char class validation.
  - Web: query sanitization, safe search, timeout, result sanitization.
- Pipeline: maintain injection patterns; monitor logs; rate limiting.


