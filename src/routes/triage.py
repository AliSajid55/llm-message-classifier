import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from src.llm.schema import TriageRequest, TriageResponse
from src.llm.client import get_client, get_model

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

    content = completion.choices[0].message.content
    if content is None:
        raise HTTPException(status_code=500, detail="Model returned empty response")
    return TriageResponse.model_validate_json(content)
