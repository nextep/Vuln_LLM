# Tasks

## Phase 1: Foundation (P0)
- [ ] Extend `test_cases.json` schema with `model_tag`, `level`, `rubric_weights`
  - AC: JSON validates; existing tests load; model tags optional but supported
- [ ] Challenges blueprint (`/challenges`, `/challenge/<id>`, POST attempt)
  - AC: Pages render; submission posts; server calls OpenWebUI; returns score/feedback
- [ ] Evaluators for LLM01 (low/medium/high/impossible)
  - AC: Injection success/failure detected per level rules

## Phase 2: Evaluators (P0/P1)
- [ ] LLM02: insecure output (XSS indicators)
- [ ] LLM03: training data poisoning (use existing)
- [ ] LLM04: model DoS (pattern/latency heuristics)
- [ ] LLM05: supply chain (malicious code patterns)
- [ ] LLM06: sensitive info (use existing)
- [ ] LLM07: plugin design (cmd inj, path traversal, SQLi)
- [ ] LLM08: excessive agency (use existing)
- [ ] LLM09: overreliance (use existing)
- [ ] LLM10: model theft (repetition/architecture reveal indicators)
  - AC: Per evaluator unit tests pass; rubric outputs stable

## Phase 3: Progress & Analytics (P1)
- [ ] Progress dashboard `/progress`: scores, badges, unlocks
- [ ] Attempts log storage (SQLite or JSON log)
- [ ] Instructor analytics aggregations
  - AC: per-user metrics; cohort view

## Phase 4: Anti-Cheat (P1)
- [ ] Rate limiting, cooldown, IP/session tracking
- [ ] Random seeds & parameterization per attempt
- [ ] Hide raw responses for sensitive tests; filter display
  - AC: enforced server-side; bypass attempts logged

## Phase 5: Validation & UX (P2)
- [ ] Validator for OpenWebUI model presence; UI badge on catalog
- [ ] Polished templates; hints/source gating; accessibility
- [ ] Docs & onboarding

## Cross-cutting
- [ ] SECURITY.md controls implemented
- [ ] Unit tests for evaluators, services
- [ ] Lint & type-check for new Python modules