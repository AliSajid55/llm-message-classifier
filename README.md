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

## Kill Switch

Set `LLM_ENABLED=false` in `.env` to use stub mode (no LLM calls).

