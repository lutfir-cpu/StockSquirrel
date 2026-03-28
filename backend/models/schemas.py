from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    title: str
    url: str
    text: str


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, description="Stock ticker symbol")
    evidence: list[EvidenceItem] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    ticker: str
    signal: str
    recommendation: str
    summary: str
    key_drivers: list[str]
    risks: list[str]
    confidence: float
    sources: list[EvidenceItem]
