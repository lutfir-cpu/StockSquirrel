from fastapi import APIRouter, HTTPException
import httpx

from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.research_service import analyze_ticker
import time

# Simple in-memory cache for the SEC tickers to avoid repeated slow requests
TICKERS_CACHE: dict | None = None
TICKERS_CACHE_TS = 0
TICKERS_CACHE_TTL = 60 * 60  # 1 hour

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        print(f"Received analysis request for {request.ticker} with {len(request.evidence)} evidence items.")
        result = await analyze_ticker(request.ticker, request.evidence)
        return AnalyzeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Error occurred while analyzing {request.ticker}: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/tickers")
async def get_tickers():
    """Proxy endpoint to fetch SEC company_tickers.json server-side (avoids CORS).

    Returns the raw JSON as received from the SEC.
    """
    # Return cached value when recent
    global TICKERS_CACHE, TICKERS_CACHE_TS
    now = time.time()
    if TICKERS_CACHE and (now - TICKERS_CACHE_TS) < TICKERS_CACHE_TTL:
        return TICKERS_CACHE

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers={"User-Agent": "StockSquirrel/0.1 (dev) contact:you@example.com"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            # cache the result
            TICKERS_CACHE = data
            TICKERS_CACHE_TS = time.time()
            return data
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else 502
            raise HTTPException(status_code=status, detail="SEC request failed")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="Failed to reach SEC") from e
