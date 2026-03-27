async def analyze_ticker(ticker: str) -> dict:
    normalized_ticker = ticker.strip().upper()
    return {
            "ticker": normalized_ticker,
            "signal": "unknown",
            "recommendation": "Insufficient Evidence",
            "summary": f"No relevant web evidence was found for {normalized_ticker}.",
            "key_drivers": [],
            "risks": ["Insufficient evidence from the open web"],
            "confidence": 0.0,
            "sources": [],
    }