"""FastAPI app exposing the GoogleScraper via HTTP."""

from typing import List

from fastapi import FastAPI, Query
from pydantic import BaseModel

from gsearch import GoogleScraper


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


scraper = GoogleScraper()
app = FastAPI(title="Gsearch", description="Google scraping API", version="1.0.0")


@app.get("/health", summary="Health check")
def health_check() -> dict:
    """Simple endpoint used for uptime monitoring."""
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse, summary="Perform a Google search")
def search(
    query: str = Query(..., min_length=1, description="De zoekterm om naar te zoeken."),
    num_results: int = Query(
        10,
        ge=1,
        le=20,
        description="Aantal resultaten om terug te geven (1-20).",
    ),
) -> SearchResponse:
    """Run the scraper for the provided query and return structured results."""
    results = scraper.search(query, num_results=num_results)
    return SearchResponse(query=query, results=results)
