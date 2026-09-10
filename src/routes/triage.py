import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from src.llm.schema import TriageRequest, TriageResponse
from src.llm.client import get_client, get_model, call_with_retry, log_call
from src.llm.parse_repair import parse_and_validate, log_quarantine

load_dotenv(override=True)

router = APIRouter()

PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

cache: dict[str, TriageResponse] = {}
CACHE_MAX_SIZE = 100


def get_cache_key(text: str, prompt_version: str) -> str:
    raw = f"{text}:{prompt_version}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_prompt(version="v1"):
    prompt_file = PROMPT_DIR / f"triage-{version}.md"
    return prompt_file.read_text()


@router.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest, prompt_version: str = Query(default="v1", regex="^(v1|v2)$")):
    if os.environ.get("LLM_ENABLED") == "false":
        return TriageResponse(
            category="other",
            urgency="normal",
            confidence=0.0,
            reason="service disabled"
        )

    cache_key = get_cache_key(request.text, prompt_version)

    if cache_key in cache:
        return cache[cache_key]

    system_prompt = load_prompt(prompt_version)
    client = get_client()
    model = get_model()

    result, error = call_with_retry(
        client, model,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text},
        ]
    )

    if error:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {error}")

    log_call(model, result["input_tokens"], result["output_tokens"], result["duration_ms"], False)

    response, parse_error = parse_and_validate(result["content"], request.text)

    if response is not None:
        if len(cache) >= CACHE_MAX_SIZE:
            cache.pop(next(iter(cache)))
        cache[cache_key] = response
        return response

    repair_result, repair_error = call_with_retry(
        client, model,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text},
            {"role": "assistant", "content": result["content"]},
            {"role": "user", "content": f"Your previous answer was rejected for this reason: {parse_error}. Return only corrected JSON matching the schema."},
        ]
    )

    if repair_error:
        log_quarantine(result["content"], parse_error or "Unknown error", prompt_version, request.text)
        raise HTTPException(status_code=422, detail=f"Model output invalid: {parse_error}")

    log_call(model, repair_result["input_tokens"], repair_result["output_tokens"], repair_result["duration_ms"], True)

    response, repair_parse_error = parse_and_validate(repair_result["content"], request.text)

    if response is not None:
        if len(cache) >= CACHE_MAX_SIZE:
            cache.pop(next(iter(cache)))
        cache[cache_key] = response
        return response

    log_quarantine(repair_result["content"], repair_parse_error or "Unknown error", prompt_version, request.text)
    raise HTTPException(status_code=422, detail=f"Model output invalid: {repair_parse_error}")
