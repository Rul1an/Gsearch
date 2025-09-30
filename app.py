"""FastAPI app exposing the GoogleScraper via HTTP."""

import logging
from typing import List

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
scraper = GoogleScraper()
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
