# Architecture

- Client: Challenge UI pages (catalog/detail/progress)
- Server: Flask routes; evaluators; anti-cheat; progress service
- Backend: OpenWebUI over `/api` with auth header

## Request Flow
1) User opens challenge detail `/challenge/<id>`
2) Submits attempt → POST to server
3) Server calls OpenWebUI model specified by test `model_tag`
4) Evaluator grades response; applies rubric
5) Attempt logged; feedback returned; progress updated

## Anti-Cheat
- No model tags or endpoints in client
- Rate limit & cooldown
- Randomized seeds in prompts
- Selective response redaction

## Components
- `challenges_blueprint`: routes
- `evaluators`: registry + functions
- `progress_service`: persistence & badges
- `anti_cheat`: limits, heuristics
- `validator`: checks OpenWebUI has required models