import json
from typing import Any


def _normalize_chat_response(content: str, ticker: str) -> dict[str, Any]:
    text = content.strip()

    if not text:
        text = f"No summary was returned for {ticker}."

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "signal": "unknown",
            "recommendation": "Summary Only",
            "summary": text,
            "key_drivers": [],
            "risks": [],
            "confidence": 0.0,
        }

    return {
        "signal": str(parsed.get("signal", "unknown")),
        "recommendation": str(parsed.get("recommendation", "Summary Only")),
        "summary": str(parsed.get("summary", text)),
        "key_drivers": [str(item) for item in parsed.get("key_drivers", [])],
        "risks": [str(item) for item in parsed.get("risks", [])],
        "confidence": float(parsed.get("confidence", 0.0)),
    }


async def analyze_evidence(ticker: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Ask OpenAI to summarize available evidence for a ticker and return
    a structured analysis payload.
    """
    try:
        from openai import AsyncOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'openai' package is not installed. Install it before using /analyze."
        ) from exc

    try:
        from settings import settings
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'pydantic-settings' package is not installed. Install it before using /analyze."
        ) from exc

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to your .env file before using /analyze."
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    normalized_ticker = ticker.strip().upper()

    json_shape = (
        '{"signal":"unknown","recommendation":"Summary Only","summary":"string",'
        '"key_drivers":["string"],"risks":["string"],"confidence":0.0}'
    )

    if evidence:
        evidence_text = "\n\n".join(
            [
                "\n".join(
                    [
                        f"Title: {item.get('title', 'Untitled')}",
                        f"URL: {item.get('url', '')}",
                        f"Text: {item.get('text', '')}",
                    ]
                )
                for item in evidence
            ]
        )
        print(evidence_text)
        user_prompt = (
            f"Analyze the stock ticker {normalized_ticker} using the following evidence:\n\n"
            f"{evidence_text}\n\n"
            "Return only valid JSON with exactly these keys: "
            f"{json_shape}. "
            "Set signal to one of positive, neutral, negative, or unknown. "
            "Set recommendation to a short label such as Buy, Hold, Sell, or Summary Only. "
            "Keep summary concise. "
            "Make key_drivers a list of short strings. "
            "Make risks a list of short strings. "
            "Make confidence a number between 0 and 1. "
            "Do not return markdown, prose outside JSON, or code fences."
        )
    else:
        user_prompt = (
            f"No evidence was supplied for ticker {normalized_ticker}. "
            "Provide a concise general stock summary anyway based on your knowledge, "
            "and make clear that it is a general overview rather than evidence-backed research. "
            "Return only valid JSON with exactly these keys: "
            f"{json_shape}. "
            "Do not return markdown, prose outside JSON, or code fences."
        )

    print("Analysing using OpenAI...")
    response = await client.chat.completions.create(
        model="gpt-5.4",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful stock research assistant. "
                    "When evidence is provided, use it. "
                    "When evidence is not provided, still provide a concise general stock summary. "
                    "Keep the answer practical and brief. "
                    "Always return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    content = response.choices[0].message.content or ""
    return _normalize_chat_response(content, normalized_ticker)
