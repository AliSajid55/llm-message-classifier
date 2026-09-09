import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from src.llm.schema import TriageRequest, TriageResponse
from src.llm.client import get_client, get_model
from src.llm.parse_repair import parse_and_validate, log_quarantine

load_dotenv(override=True)

router = APIRouter()

PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(version="v1"):
    prompt_file = PROMPT_DIR / f"triage-{version}.md"
    return prompt_file.read_text()


@router.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest):
    if os.environ.get("LLM_STUB") == "1":
        return TriageResponse(
            category="other",
            urgency="normal",
            confidence=0.0,
            reason="stub mode - no LLM call"
        )

    system_prompt = load_prompt()
    client = get_client()
    model = get_model()

    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text},
        ],
    )

    raw = completion.choices[0].message.content or ""
    response, error = parse_and_validate(raw, request.text)

    if response is not None:
        return response

    repair_completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": f"Your previous answer was rejected for this reason: {error}. Return only corrected JSON matching the schema."},
        ],
    )

    repair_raw = repair_completion.choices[0].message.content or ""
    response, repair_error = parse_and_validate(repair_raw, request.text)

    if response is not None:
        return response

    log_quarantine(repair_raw, repair_error or "Unknown error", "v1", request.text)
    raise HTTPException(status_code=422, detail=f"Model output invalid: {repair_error}")
