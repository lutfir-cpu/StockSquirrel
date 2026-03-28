from typing import Any

import httpx


TINYFISH_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"


def _normalize_evidence_items(payload: Any, fallback_url: str) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("evidence"), list):
            candidates = payload["evidence"]
        elif isinstance(payload.get("items"), list):
            candidates = payload["items"]
        else:
            candidates = [payload]
    elif isinstance(payload, list):
        candidates = payload
    else:
        candidates = []

    normalized: list[dict[str, str]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or item.get("headline") or item.get("name") or "").strip()
        url = str(item.get("url") or item.get("link") or fallback_url).strip() or fallback_url
        text = str(
            item.get("text")
            or item.get("summary")
            or item.get("description")
            or item.get("reason")
            or ""
        ).strip()

        if not title and not text:
            continue

        normalized.append(
            {
                "title": title or "Untitled evidence",
                "url": url,
                "text": text or title or "No additional detail provided.",
            }
        )

    return normalized


async def _run_tinyfish(url: str, goal: str, api_key: str) -> list[dict[str, str]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            TINYFISH_RUN_URL,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            json={
                "url": url,
                "goal": goal,
                "browser_profile": "lite",
                "api_integration": "stocksquirrel",
            },
        )

    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "COMPLETED":
        error = payload.get("error") or {"message": "TinyFish run did not complete successfully."}
        raise RuntimeError(str(error.get("message") or error))

    return _normalize_evidence_items(payload.get("result"), fallback_url=url)


async def gather_ticker_evidence(ticker: str) -> list[dict[str, str]]:
    try:
        from settings import settings
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'pydantic-settings' package is not installed. Install it before using TinyFish."
        ) from exc

    if not settings.tinyfish_api_key:
        raise RuntimeError(
            "TINYFISH_API_KEY is not configured. Add it to your .env file before using /analyze."
        )

    normalized_ticker = ticker.strip().upper()
    tasks = [
        {
            "url": f"https://finance.yahoo.com/quote/{normalized_ticker}",
            "goal": (
                f"Collect up to 3 evidence items about the stock ticker {normalized_ticker} from this page. "
                "Return JSON with an 'evidence' array. Each item must have: title, url, text. "
                "Focus on visible company details, price action, valuation data, analyst snippets, or headlines."
            ),
        },
        {
            "url": f"https://finance.yahoo.com/quote/{normalized_ticker}/news",
            "goal": (
                f"Collect up to 5 recent news evidence items relevant to stock ticker {normalized_ticker}. "
                "Return JSON with an 'evidence' array. Each item must have: title, url, text. "
                "Use the article link if visible. Keep text to one or two sentences on why the item matters."
            ),
        },
    ]

    evidence: list[dict[str, str]] = []
    for task in tasks:
        try:
            evidence.extend(
                await _run_tinyfish(
                    url=task["url"],
                    goal=task["goal"],
                    api_key=settings.tinyfish_api_key,
                )
            )
        except Exception:
            continue

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in evidence:
        key = (item["title"], item["url"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped
