# GPT-5 Challenge UI Initiative

## Goal
Create a dedicated challenge UI that uses your OpenWebUI custom models per vulnerability and difficulty, prevents cheating, and delivers a scored, feedback-driven learning experience aligned with `ASSESSMENT_GUIDE.md`.

## Key Outcomes
- Server-controlled challenges; no direct OpenWebUI access for users
- Difficulty-tagged custom models from `openwebui_templates/`
- Scored attempts with rubrics, hints, unlocks, progress, analytics
- Anti-cheat, rate limits, randomized seeds, and model presence validator

## Deliverables
- `PLAN.md`, `TASKS.md`, `ARCHITECTURE.md`, `SCHEMA.md`, `ENDPOINTS.md`, `SECURITY.md`, `VALIDATION.md`
- Python stubs in `GPT5/STUBS/` for blueprints, evaluators, progress, anti-cheat
- Mermaid diagram of system architecture

## Next Steps
- Review `PLAN.md` and `TASKS.md`
- Approve model tag conventions and manifest schema changes
- Implement stubs → integrate with existing app