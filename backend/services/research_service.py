from clients.openai_client import analyze_evidence
from clients.tinyfish_client import gather_ticker_evidence, stream_ticker_evidence


def _build_analysis_response(
    normalized_ticker: str, analysis: dict, evidence_items: list[dict]
) -> dict:
    return {
        "ticker": normalized_ticker,
        "signal": analysis["signal"],
        "recommendation": analysis["recommendation"],
        "summary": analysis["summary"],
        "key_drivers": analysis["key_drivers"],
        "risks": analysis["risks"],
        "confidence": analysis["confidence"],
        "sources": evidence_items,
    }


async def analyze_ticker(ticker: str, evidence: list | None = None) -> dict:
    normalized_ticker = ticker.strip().upper()
    provided_evidence = [
        item.model_dump() if hasattr(item, "model_dump") else item
        for item in (evidence or [])
    ]
    gathered_evidence = await gather_ticker_evidence(normalized_ticker)
    print("Gathered evidence")
    evidence_items = provided_evidence + gathered_evidence
    analysis = await analyze_evidence(normalized_ticker, evidence_items)

    return _build_analysis_response(normalized_ticker, analysis, evidence_items)


async def stream_ticker_analysis(ticker: str, evidence: list | None = None):
    normalized_ticker = ticker.strip().upper()
    provided_evidence = [
        item.model_dump() if hasattr(item, "model_dump") else item
        for item in (evidence or [])
    ]

    yield {"type": "status", "message": f"Starting evidence gathering for {normalized_ticker}."}

    gathered_evidence: list[dict] = []
    async for event in stream_ticker_evidence(normalized_ticker):
        if event["type"] == "complete":
            gathered_evidence = event["evidence"]
            continue
        yield event

    evidence_items = provided_evidence + gathered_evidence
    yield {"type": "status", "message": f"Analysing {normalized_ticker} with OpenAI."}
    analysis = await analyze_evidence(normalized_ticker, evidence_items)
    yield {
        "type": "analysis",
        "analysis": _build_analysis_response(normalized_ticker, analysis, evidence_items),
    }
