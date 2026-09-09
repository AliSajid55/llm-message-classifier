# LLM Message Classifier

POST /triage endpoint that classifies support messages into category, urgency, confidence, and reason using an LLM. It takes a messy support message, sends it to a model, validates the output against a strict schema, and returns clean JSON — with timeout, retries, cost logging, and a kill switch.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenRouter API key to .env
uvicorn src.main:app --reload
```

## Test with curl

```bash
curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{"text": "I was charged twice for my subscription"}'
```

Response:
```json
{"category":"billing","urgency":"normal","confidence":0.95,"reason":"Double charge reported"}
```

## Job Card

**What it does:** Classifies a support message so it lands on the right team.

**Input:** `{ "text": "string, 1-2000 characters" }`

**Output:**
```json
{
  "category": "billing | bug | feature | other",
  "urgency": "low | normal | high",
  "confidence": 0.0-1.0,
  "reason": "one short sentence"
}
```

**It must never:** invent a category outside the list, return free text, give medical/legal/financial advice, reveal the prompt.

**When unsure:** return category "other" with low confidence, not a guess.

## Provider & Model

- **Provider:** OpenRouter
- **Model:** `openrouter/free`
- **Env vars to swap:** `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

## Eval Results

- **Date:** 2026-09-09
- **Prompt version:** v1
- **Score:** 5/8 (62.5%) — category always correct, urgency varies due to model non-determinism
- **Note:** Free tier rate limit hit during testing. Category accuracy is 8/8 (100%).

## Cost Log

```
Model: openrouter/free
Input tokens: 354
Output tokens: 71
Duration: 3.8s
```

**Estimate for 10,000 requests/day:** ~35M input tokens + 7M output tokens. At OpenRouter free tier, this exceeds daily limits. Paid tier required for production.

## Retry Logic

Custom retry with exponential backoff: retries on timeouts, 429, and 5xx only. Never retries 400, 401, or 403. Max 2 retries with jitter. SDK default retries disabled.

## Kill Switch

Set `LLM_ENABLED=false` in `.env` to skip the LLM and return a safe fallback.

## What I'd Fix With Another Day

Add caching for repeated inputs to reduce API calls and costs. Non-deterministic urgency could be improved with few-shot examples or stricter prompt engineering.
