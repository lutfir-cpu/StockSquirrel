import logging
from typing import Any

import httpx


TINYFISH_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"
TINYFISH_FALLBACK_URL = "https://agent.tinyfish.ai"
TINYFISH_SEARCH_URL = "https://duckduckgo.com/"
TINYFISH_TIMEOUT_SECONDS = 300.0

logger = logging.getLogger(__name__)


def _normalize_evidence_items(payload: Any, fallback_url: str) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        normalized = []
        if isinstance(payload.get("evidence"), list):
            candidates = payload["evidence"]
        elif isinstance(payload.get("items"), list):
            candidates = payload["items"]
        else:
            candidates = [payload]
    elif isinstance(payload, list):
        normalized = []
        candidates = payload
    else:
        normalized = []
        candidates = []

    existing = {
        (item["title"].strip().lower(), item["text"].strip().lower()) for item in normalized
    }

    for item in candidates:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or item.get("headline") or item.get("name") or "").strip()
        url = str(
            item.get("url") or item.get("link") or item.get("source") or fallback_url
        ).strip() or fallback_url
        text = str(
            item.get("text")
            or item.get("summary")
            or item.get("description")
            or item.get("reason")
            or ""
        ).strip()

        if not title and not text:
            continue

        normalized_item = {
            "title": title or "Untitled evidence",
            "url": url,
            "text": text or title or "No additional detail provided.",
        }
        key = (
            normalized_item["title"].strip().lower(),
            normalized_item["text"].strip().lower(),
        )
        if key in existing:
            continue
        existing.add(key)
        normalized.append(normalized_item)

    return normalized


async def _run_tinyfish(url: str, goal: str, api_key: str) -> list[dict[str, str]]:
    try:
        async with httpx.AsyncClient(timeout=TINYFISH_TIMEOUT_SECONDS) as client:
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
    except httpx.ReadTimeout as exc:
        raise RuntimeError(
            f"TinyFish request timed out after {int(TINYFISH_TIMEOUT_SECONDS)} seconds"
        ) from exc

    if response.is_error:
        raise RuntimeError(f"TinyFish request failed with HTTP {response.status_code}")

    payload = response.json()

    if payload.get("status") != "COMPLETED":
        error = payload.get("error") or {"message": "TinyFish run did not complete successfully."}
        raise RuntimeError(str(error.get("message") or error))

    result = payload.get("result") or payload.get("resultJson")
    if not result:
        logger.warning("TinyFish completed for %s but returned no result.", url)
        return []

    if isinstance(result, dict) and (result.get("status") == "failure" or result.get("error")):
        raise RuntimeError(
            str(result.get("reason") or result.get("error") or "TinyFish goal not achieved")
        )

    normalized_items = _normalize_evidence_items(result, fallback_url=url)
    if not normalized_items:
        logger.warning(
            "TinyFish completed for %s but returned no normalized evidence.",
            url,
        )

    return normalized_items


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
            "url": TINYFISH_SEARCH_URL,
            "goal": (
                f"Collect up to 6 relevant latest news or evidence items about stock ticker {normalized_ticker}. "
                "Return JSON with an 'evidence' array. Each item must have: title, source, and text. "
                "Focus on company performance, price action, valuation, analyst opinions, recent news, and headlines. "
                "Summarize the key drivers that seem to be influencing the stock, such as earnings projections, recent announcements, "
                "market sentiment, or external factors like regulations or competition. "
                "Also, note any risks or challenges mentioned, such as economic conditions, potential volatility, or industry competition. "
                "Make sure the 'source' field captures the full url where the information is coming from. If it is from the url https://duckduckgo.com/, do not return as a source url."
                "Use this exact shape: "
                '{"summary":{"key_drivers":[{"name":"string","description":"string"}],"risks":[{"name":"string","description":"string"}]},"evidence":[{"title":"string","source":"string","text":"string"}]}. '
                "Focus on company performance, valuation, analyst views, recent news, key drivers, and risks. "
                "Do not return markdown, prose, or code fences."
            ),
        },
    ]

    evidence: list[dict[str, str]] = []
    for index, task in enumerate(tasks, start=1):
        try:
            task_evidence = await _run_tinyfish(
                url=task["url"],
                goal=task["goal"],
                api_key=settings.tinyfish_api_key,
            )
            logger.info(
                "TinyFish task %s for %s returned %s items.",
                index,
                normalized_ticker,
                len(task_evidence),
            )
            evidence.extend(task_evidence)
        except Exception as exc:
            logger.error(
                "TinyFish task %s for %s failed: %s: %r",
                index,
                normalized_ticker,
                type(exc).__name__,
                exc,
            )
            continue

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in evidence:
        key = (item["title"].strip().lower(), item["text"].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    print(f"Gathered evidence for {normalized_ticker}: {len(deduped)} items")
    if deduped:
        print(f"First evidence item for {normalized_ticker}: {deduped[0]}")

    return deduped
