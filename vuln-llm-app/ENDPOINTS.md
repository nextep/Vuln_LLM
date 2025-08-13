# Endpoints

## GET /challenges
- 200: HTML catalog

## GET /challenge/<id>
- 200: HTML detail (no tags, no backend exposure)

## POST /challenge/<id>/attempt
- Req: form `{ payload, (optional) image_file }`
- Res: JSON `{ score, feedback, indicators, duration_ms }`
- Errors: 400 invalid input; 429 rate limited; 500 failure

## GET /progress
- 200: HTML dashboard with badges/scores

## GET /challenge/<id>/hint
- 200: JSON/HTML snippet (gated by rules)

## GET /challenge/<id>/source
- 200: JSON/HTML (partial source; safe redaction)