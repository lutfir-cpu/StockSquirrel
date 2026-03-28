import asyncio
import logging
from typing import Any

import httpx


TINYFISH_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"
TINYFISH_RUN_ASYNC_URL = "https://agent.tinyfish.ai/v1/automation/run-async"
TINYFISH_RUNS_URL = "https://agent.tinyfish.ai/v1/runs"
TINYFISH_FALLBACK_URL = "https://agent.tinyfish.ai"
TINYFISH_SEARCH_URL = "https://duckduckgo.com/"
TINYFISH_TIMEOUT_SECONDS = 300.0
TINYFISH_POLL_INTERVAL_SECONDS = 2.0
TINYFISH_RUN_LOOKUP_RETRIES = 3

logger = logging.getLogger(__name__)


def _get_tinyfish_api_key() -> str:
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

    return settings.tinyfish_api_key


def _tinyfish_headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }


def _build_tinyfish_tasks(normalized_ticker: str) -> list[dict[str, str]]:
    return [
        {
            "url": TINYFISH_SEARCH_URL,
            "goal": (
                f"Collect up to 1 relevant latest news or evidence items about stock ticker {normalized_ticker}. "
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


def _dedupe_evidence(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in evidence:
        key = (item["title"].strip().lower(), item["text"].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def _extract_tinyfish_result(payload: dict[str, Any], fallback_url: str) -> list[dict[str, str]]:
    if payload.get("status") != "COMPLETED":
        error = payload.get("error") or {"message": "TinyFish run did not complete successfully."}
        raise RuntimeError(str(error.get("message") or error))

    result = payload.get("result") or payload.get("resultJson")
    if not result:
        logger.warning("TinyFish completed for %s but returned no result.", fallback_url)
        return []

    if isinstance(result, dict) and (result.get("status") == "failure" or result.get("error")):
        raise RuntimeError(
            str(result.get("reason") or result.get("error") or "TinyFish goal not achieved")
        )

    normalized_items = _normalize_evidence_items(result, fallback_url=fallback_url)
    if not normalized_items:
        logger.warning(
            "TinyFish completed for %s but returned no normalized evidence.",
            fallback_url,
        )

    return normalized_items


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
                headers=_tinyfish_headers(api_key),
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
    return _extract_tinyfish_result(payload, fallback_url=url)


async def _start_tinyfish_run(url: str, goal: str, api_key: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=TINYFISH_TIMEOUT_SECONDS) as client:
            response = await client.post(
                TINYFISH_RUN_ASYNC_URL,
                headers=_tinyfish_headers(api_key),
                json={
                    "url": url,
                    "goal": goal,
                    "browser_profile": "lite",
                    "api_integration": "stocksquirrel",
                },
            )
    except httpx.ReadTimeout as exc:
        raise RuntimeError(
            f"TinyFish async request timed out after {int(TINYFISH_TIMEOUT_SECONDS)} seconds"
        ) from exc

    if response.is_error:
        raise RuntimeError(f"TinyFish async request failed with HTTP {response.status_code}")

    payload = response.json()
    run_id = str(payload.get("run_id") or "").strip()
    if not run_id:
        raise RuntimeError("TinyFish async request did not return a run_id")

    return run_id


async def _get_tinyfish_run(run_id: str, api_key: str) -> dict[str, Any]:
    last_status_code: int | None = None

    for attempt in range(1, TINYFISH_RUN_LOOKUP_RETRIES + 1):
        async with httpx.AsyncClient(timeout=TINYFISH_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{TINYFISH_RUNS_URL}/{run_id}",
                headers=_tinyfish_headers(api_key),
            )

        if not response.is_error:
            return response.json()

        last_status_code = response.status_code
        if response.status_code not in {502, 503, 504}:
            raise RuntimeError(f"TinyFish run lookup failed with HTTP {response.status_code}")

        logger.warning(
            "TinyFish run lookup for %s failed with HTTP %s (attempt %s/%s).",
            run_id,
            response.status_code,
            attempt,
            TINYFISH_RUN_LOOKUP_RETRIES,
        )
        if attempt < TINYFISH_RUN_LOOKUP_RETRIES:
            await asyncio.sleep(TINYFISH_POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"TinyFish run lookup failed with HTTP {last_status_code}")


async def stream_ticker_evidence(ticker: str):
    api_key = _get_tinyfish_api_key()
    normalized_ticker = ticker.strip().upper()
    tasks = _build_tinyfish_tasks(normalized_ticker)

    evidence: list[dict[str, str]] = []
    for index, task in enumerate(tasks, start=1):
        yield {
            "type": "status",
            "message": f"Starting TinyFish task {index} for {normalized_ticker}.",
        }
        run_id = await _start_tinyfish_run(task["url"], task["goal"], api_key)
        yield {"type": "status", "message": f"TinyFish run {run_id} started."}

        last_status: str | None = None
        streaming_url_sent = False
        while True:
            run = await _get_tinyfish_run(run_id, api_key)

            streaming_url = str(run.get("streaming_url") or "").strip()
            if streaming_url and not streaming_url_sent:
                streaming_url_sent = True
                yield {
                    "type": "preview_url",
                    "streaming_url": streaming_url,
                }

            status = str(run.get("status") or "").strip().upper()
            if status and status != last_status:
                last_status = status
                yield {
                    "type": "status",
                    "message": f"TinyFish run status: {status}.",
                }

            if status in {"PENDING", "RUNNING"}:
                await asyncio.sleep(TINYFISH_POLL_INTERVAL_SECONDS)
                continue

            task_evidence = _extract_tinyfish_result(run, fallback_url=task["url"])
            evidence.extend(task_evidence)
            yield {
                "type": "status",
                "message": f"TinyFish gathered {len(task_evidence)} evidence items.",
            }
            break

    deduped = _dedupe_evidence(evidence)
    print(f"Gathered evidence for {normalized_ticker}: {len(deduped)} items")
    if deduped:
        print(f"First evidence item for {normalized_ticker}: {deduped[0]}")

    yield {"type": "complete", "evidence": deduped}


async def gather_ticker_evidence(ticker: str) -> list[dict[str, str]]:
    api_key = _get_tinyfish_api_key()
    normalized_ticker = ticker.strip().upper()
    tasks = _build_tinyfish_tasks(normalized_ticker)

    evidence: list[dict[str, str]] = []
    for index, task in enumerate(tasks, start=1):
        try:
            task_evidence = await _run_tinyfish(
                url=task["url"],
                goal=task["goal"],
                api_key=api_key,
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

    deduped = _dedupe_evidence(evidence)

    print(f"Gathered evidence for {normalized_ticker}: {len(deduped)} items")
    if deduped:
        print(f"First evidence item for {normalized_ticker}: {deduped[0]}")

    return deduped
