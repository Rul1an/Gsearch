"""FastAPI app exposing the GoogleScraper via HTTP."""

import logging
import os
from typing import List, Optional, Sequence

from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from gsearch import GoogleScraper, CaptchaDetectedError


def _configure_logging() -> None:
    level_name = os.getenv("GSEARCH_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level)


_configure_logging()


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


s_logger = logging.getLogger("gsearch.app")


def _split_env_list(value: Optional[str]) -> List[str]:
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

    max_requests_per_minute: Optional[int]
    max_requests_raw = os.getenv("GSEARCH_MAX_REQUESTS_PER_MINUTE")
    if max_requests_raw:
        try:
            parsed_max = int(max_requests_raw)
            max_requests_per_minute = parsed_max if parsed_max > 0 else None
        except ValueError:
            s_logger.warning(
                "Invalid GSEARCH_MAX_REQUESTS_PER_MINUTE='%s'; ignoring",
                max_requests_raw,
            )
            max_requests_per_minute = None
    else:
        max_requests_per_minute = None

    max_backoff_seconds = 30.0
    max_backoff_raw = os.getenv("GSEARCH_MAX_BACKOFF_SECONDS")
    if max_backoff_raw:
        try:
            max_backoff_seconds = max(float(max_backoff_raw), 0.0)
        except ValueError:
            s_logger.warning(
                "Invalid GSEARCH_MAX_BACKOFF_SECONDS='%s'; ignoring",
                max_backoff_raw,
            )

    backoff_jitter = 0.5
    jitter_raw = os.getenv("GSEARCH_BACKOFF_JITTER")
    if jitter_raw:
        try:
            backoff_jitter = max(float(jitter_raw), 0.0)
        except ValueError:
            s_logger.warning("Invalid GSEARCH_BACKOFF_JITTER='%s'; ignoring", jitter_raw)

    return GoogleScraper(
        delay=delay,
        proxies=proxies,
        user_agents=user_agents,
        max_requests_per_minute=max_requests_per_minute,
        max_backoff_seconds=max_backoff_seconds,
        backoff_jitter=backoff_jitter,
    )


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
