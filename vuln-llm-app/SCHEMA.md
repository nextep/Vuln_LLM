# Schemas

## test_cases.json (extension)
```json
{
  "vulnerabilities": [
    {
      "id": "LLM01",
      "name": "Prompt Injection",
      "levels": {
        "low": {
          "model_tag": "llm01-level1",
          "rubric_weights": {"exec": 0.5, "doc": 0.2, "under": 0.2, "ethics": 0.1},
          "tests": [
            {"id": "llm01_low_001", "name": "Direct System Prompt Extraction", "payload": "...", "expected_outcome": "...", "hint": "..."}
          ]
        }
      }
    }
  ]
}
```

## Attempt Record
```json
{
  "user_id": "...",
  "challenge_id": "llm01_low_001",
  "payload": "user input...",
  "response": "model output...",
  "score": 0.8,
  "rubric": {"exec": 0.6, "doc": 0.1, "under": 0.1, "ethics": 0.0},
  "indicators": ["pattern:system prompt"],
  "ts": "2025-08-04T02:30:00Z",
  "duration_ms": 2300,
  "hint_used": false
}
```

## Progress Snapshot
```json
{
  "user_id": "...",
  "badges": ["LLM01:LOW"],
  "scores": {"LLM01": 0.75},
  "levels_unlocked": {"LLM01": ["medium"]}
}
```