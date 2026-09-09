from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class TriageResponse(BaseModel):
    category: str = Field(..., pattern=r"^(billing|bug|feature|other)$")
    urgency: str = Field(..., pattern=r"^(low|normal|high)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
