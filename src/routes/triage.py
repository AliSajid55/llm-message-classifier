import os
from fastapi import APIRouter, HTTPException
from src.llm.schema import TriageRequest, TriageResponse

router = APIRouter()

STUB_RESPONSE = TriageResponse(
    category="other",
    urgency="normal",
    confidence=0.0,
    reason="stub mode - no LLM call"
)


@router.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest):
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    return TriageResponse(
        category="other",
        urgency="normal",
        confidence=0.0,
        reason="live mode not implemented yet"
    )
