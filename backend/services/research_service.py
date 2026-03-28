from clients.openai_client import analyze_evidence
# from clients.tinyfish_client import gather_ticker_evidence


async def analyze_ticker(ticker: str, evidence: list | None = None) -> dict:
    normalized_ticker = ticker.strip().upper()
    provided_evidence = [
        item.model_dump() if hasattr(item, "model_dump") else item
        for item in (evidence or [])
    ]
    # gathered_evidence = await gather_ticker_evidence(normalized_ticker)
    evidence_items = provided_evidence
    analysis = await analyze_evidence(normalized_ticker, evidence_items)

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
