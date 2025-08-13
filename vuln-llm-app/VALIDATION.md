# OpenWebUI Model Validation Plan

## Purpose
Ensure all required `model_tag`s in `test_cases.json` exist in OpenWebUI before enabling challenges.

## Steps
1. Load `test_cases.json`; collect unique `model_tag`s
2. Call OpenWebUI `/api/models` with auth; collect available IDs/names
3. Compare sets; record missing tags
4. Show badge in catalog (green if all present; yellow with list if missing)
5. Optional: export a fix list and link to import scripts (`openwebui_templates/`)

## CLI Stub (future)
- `python -m tools.validate_models --test-manifest test_cases.json`