"""FastAPI app exposing the GoogleScraper via HTTP."""

import logging
import os
from typing import List, Sequence

from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from gsearch import GoogleScraper, CaptchaDetectedError


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


s_logger = logging.getLogger("gsearch.app")


def _split_env_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_scraper_from_env() -> GoogleScraper:
    delay_raw = os.getenv("GSEARCH_DELAY", "1.0")
    try:
        delay = max(float(delay_raw), 0.0)
    except ValueError:
        s_logger.warning("Invalid GSEARCH_DELAY='%s'; falling back to 1.0", delay_raw)
        delay = 1.0

    proxies = _split_env_list(os.getenv("GSEARCH_PROXIES"))
    user_agents: Sequence[str] = _split_env_list(os.getenv("GSEARCH_USER_AGENTS"))

    return GoogleScraper(delay=delay, proxies=proxies, user_agents=user_agents)


scraper = build_scraper_from_env()
app = FastAPI(title="Gsearch", description="Google scraping API", version="1.0.0")


@app.get("/health", summary="Health check")
def health_check() -> dict:
    """Simple endpoint used for uptime monitoring."""
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse, summary="Perform a Google search")
def search(
    query: str = Query(..., min_length=1, description="The search term to query for"),
    num_results: int = Query(
        10,
        ge=1,
        le=20,
        description="Number of results to return (1-20)",
    ),
) -> SearchResponse:
    """Run the scraper for the provided query and return structured results."""
    try:
        results = scraper.search(query, num_results=num_results)
    except CaptchaDetectedError as exc:
        s_logger.warning("CAPTCHA detected for query '%s': %s", query, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "query": query,
                "error": "captcha_detected",
                "detail": str(exc),
            },
        )

    return SearchResponse(query=query, results=results)
