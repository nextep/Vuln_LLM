# Plan: Challenge UI using OpenWebUI Custom Models

## Objectives
- Provide a structured, anti-cheat challenge platform
- Use OpenWebUI models per vulnerability and difficulty (custom templates)
- Align scoring/rubrics with `ASSESSMENT_GUIDE.md`

## Pillars
1. Challenge Delivery: catalog, detail, attempt submission, feedback
2. Evaluation & Scoring: per vulnerability evaluators; rubrics; badges
3. Anti-Cheat: server-only API, rate limits, parameter randomization
4. Analytics & Progress: attempts log, dashboards, instructor analytics
5. Validation: ensure required model tags exist in OpenWebUI

## Model Tag Strategy
- LLM01: `llm01-level1|2|3|4`
- LLM02–LLM10: `{llmXX-levelY}` consistent naming
- LLM07 Tools: `llm07-vulnerable-tools-demo`, `llm07-secure-tools-demo`
- Defined by templates in `openwebui_templates/`

## Manifest-driven Tests
- Extend `test_cases.json`
- Each test includes `model_tag`, `level`, `expected_outcome`, `hints`, `rubric_weights`

## UI Routes
- `/challenges` (catalog)
- `/challenge/<id>` (detail)
- `POST /challenge/<id>/attempt` (server graded)
- `/progress` (user dashboard)
- `/challenge/<id>/hint`, `/challenge/<id>/source` (controlled reveals)

## Backend Components
- Evaluators registry (`GPT5/STUBS/evaluators.py`)
- Challenges blueprint (`GPT5/STUBS/challenges_blueprint.py`)
- Progress service (`GPT5/STUBS/progress_service.py`)
- Anti-cheat (`GPT5/STUBS/anti_cheat.py`)
- Validator to check OpenWebUI models (`VALIDATION.md` procedure)

## Scoring & Rubrics
- Derive from `ASSESSMENT_GUIDE.md`:
  - Execution Quality, Documentation, Understanding, Ethics
- Level-based multipliers; difficulty gates unlocks

## Anti-Cheat Controls
- Server-only OpenWebUI calls; hide tags
- Attempt rate limiting, cooldown
- Randomized seeds; per-user paramization
- Similarity checks vs known solutions
- Do not display raw responses for select tests

## Analytics
- Track attempts, success rate, time-to-solve, hint usage
- Instructor analytics: cohort insights, challenge heatmap

## Milestones
1) Foundation (Catalog/Detail/Attempt + LLM01 evaluators)
2) Extend Evaluators (LLM02–LLM10)
3) Progress/Badges + Analytics
4) Anti-Cheat hardening + Validation UI badge
5) Polish UX + Docs