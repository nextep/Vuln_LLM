# Model Tag Conventions

## Per Vulnerability and Difficulty
- LLM01: `llm01-level1`, `llm01-level2`, `llm01-level3`, `llm01-level4`
- … similarly for LLM02–LLM10

## Per Secure with defenses and stop patterns
- LLM01: `llm01-secure`, `llm01-secure`, `llm01-secure`, `llm01-secure`
- … similarly for LLM02–LLM10

## LLM07 Tools
- Vulnerable: `llm07-vulnerable-tools-demo`
- Secure: `llm07-secure-tools-demo`

## Notes
- All tags are defined via `openwebui_templates/` JSON imports
- Difficulty behavior encoded in system prompts within templates