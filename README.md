# LLM Message Classifier

POST /triage endpoint that classifies support messages using an LLM.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenRouter API key to .env
```

## Run

```bash
uvicorn src.main:app --reload
```

## Endpoints

- `POST /triage` — Classifies a support message into category, urgency, confidence, and reason.

## Stub Mode

Set `LLM_STUB=1` to skip the LLM and return a hard-coded response.

## Test with curl

Valid request:
```bash
curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{"text": "My invoice is wrong"}'
```

Broken request (missing field):
```bash
curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{}'
```

## Observations

- Model classifies correctly: "charged twice" → billing, "app crashing" → bug, "dark mode" → feature
- Confidence is consistently high (0.9-0.95) for clear messages
- Temperature 0.2 gives consistent answers for same input
- Prompt file approach keeps instructions separate from code
