# Developer Notes

## Integration Steps
1. Register `challenges` blueprint in main app
2. Create templates `templates/challenges/catalog.html`, `templates/challenges/detail.html`
3. Extend `test_cases.json` per `SCHEMA.md`
4. Implement evaluator functions incrementally
5. Add progression service storage (sqlite/json)
6. Wire RateLimiter in POST attempt route
7. Add validator call on startup to compute availability badges

## Config
- Use OpenWebUI API `/api` base; auth Bearer token in server only
- Prefer `test_case['model_tag']`; fallback to difficulty map

## Testing
- Unit tests for evaluators and rate limiter
- Manual E2E: submit attempt and verify score/feedback