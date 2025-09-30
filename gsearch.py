#!/usr/bin/env python3
"""
Google Search Scraper for WBSO webcrawler
A simple Python script to scrape Google search results.
"""

import logging
import random
import requests
from bs4 import BeautifulSoup
import time
import unicodedata
import urllib.parse
from collections import deque
from itertools import cycle
from typing import Deque, Dict, Iterator, List, Optional, Sequence

logger = logging.getLogger("gsearch.scraper")


class CaptchaDetectedError(Exception):
    """Raised when Google responds with a CAPTCHA challenge."""

    pass


class GoogleScraper:
    """
    A simple Google search scraper that extracts search results.
    """
    
    def __init__(
        self,
        delay: float = 1.0,
        proxies: Optional[List[str]] = None,
        user_agents: Optional[Sequence[str]] = None,
        max_requests_per_minute: Optional[int] = None,
        max_backoff_seconds: float = 30.0,
        backoff_jitter: float = 0.5,
    ):
        """
        Initialize the Google scraper.

        Args:
            delay: Delay between requests in seconds (default: 1.0)
            proxies: Optional list of proxy URLs to rotate between.
            user_agents: Optional sequence of user-agent strings to rotate per request.
            max_requests_per_minute: Optional cap on the number of requests per rolling minute window.
            max_backoff_seconds: Maximum sleep duration during exponential backoff.
            backoff_jitter: Maximum random jitter (in seconds) added to backoff sleeps.
        """
        self.delay = delay
        self.session = requests.Session()
        
        # Proxy setup
        cleaned_proxies = [proxy for proxy in (proxies or []) if proxy]
        self._proxies = cleaned_proxies
        self._proxy_cycle: Optional[Iterator[str]] = cycle(cleaned_proxies) if cleaned_proxies else None

        # Rate limiting
        if max_requests_per_minute is not None and max_requests_per_minute <= 0:
            max_requests_per_minute = None
        self.max_requests_per_minute = max_requests_per_minute
        self._request_timestamps: Deque[float] = deque()

        # Backoff configuration
        self.max_backoff_seconds = max(max_backoff_seconds, 0.0)
        self.backoff_jitter = max(backoff_jitter, 0.0)

        # User-agent setup
        self.default_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.session.headers.update({'User-Agent': self.default_user_agent})

        filtered_user_agents = [ua for ua in user_agents or [] if ua and ua.strip()]
        self._user_agent_iter: Optional[Iterator[str]] = None
        if filtered_user_agents:
            self._user_agent_iter = cycle(filtered_user_agents)

    def _get_next_proxy(self) -> Optional[str]:
        """Retrieve the next proxy from the cycle if available."""
        if self._proxy_cycle is None:
            return None
        return next(self._proxy_cycle)

    def _apply_backoff(self, attempt_number: int) -> None:
        """Apply exponential backoff before retrying a request."""
        if self.delay <= 0:
            return

        base_delay = self.delay * (2 ** max(attempt_number - 1, 0))
        jitter = random.uniform(0.0, self.backoff_jitter) if self.backoff_jitter > 0 else 0.0
        if self.max_backoff_seconds > 0:
            sleep_seconds = min(base_delay + jitter, self.max_backoff_seconds)
        else:
            sleep_seconds = base_delay + jitter
        if sleep_seconds <= 0:
            return

        logger.debug("Backing off for %.2f seconds before retrying", sleep_seconds)
        time.sleep(sleep_seconds)

    def _prune_request_timestamps(self, current_time: float) -> None:
        """Remove timestamps that are outside the rolling one-minute window."""
        window = 60.0
        while self._request_timestamps and current_time - self._request_timestamps[0] >= window:
            self._request_timestamps.popleft()

    def _enforce_rate_limit(self) -> None:
        """Sleep when the configured rate limit would be exceeded."""
        if not self.max_requests_per_minute:
            return

        window = 60.0
        current_time = time.monotonic()
        self._prune_request_timestamps(current_time)

        if len(self._request_timestamps) >= self.max_requests_per_minute:
            earliest = self._request_timestamps[0]
            sleep_seconds = window - (current_time - earliest)
            if sleep_seconds > 0:
                logger.debug(
                    "Rate limit reached (%s/min). Sleeping for %.2f seconds",
                    self.max_requests_per_minute,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)
                current_time = time.monotonic()
                self._prune_request_timestamps(current_time)

        self._request_timestamps.append(current_time)

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        logger.info("Start search: query='%s', num_results=%d", query, num_results)
        """
        Perform a Google search and return the results.
        
        Args:
            query: The search query string
            num_results: Number of results to return (default: 10)
            
        Returns:
            List of dictionaries containing title, link, and snippet for each result
        """
        results = []

        # Encode the search query
        encoded_query = urllib.parse.quote_plus(query)

        # Construct the Google search URL
        url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"

        max_attempts = len(self._proxies) if self._proxies else 1
        attempts = 0
        response = None

        # Rotate user-agent if available
        if self._user_agent_iter is not None:
            self.session.headers['User-Agent'] = next(self._user_agent_iter)

        proxy = None
        while attempts < max_attempts:
            logger.debug("Search attempt %d/%d (proxy=%s, user-agent=%s)", attempts+1, max_attempts, proxy, self.session.headers.get('User-Agent'))
            proxy = self._get_next_proxy() if self._proxies else None
            proxies_arg = {'http': proxy, 'https': proxy} if proxy else None
            try:
                self._enforce_rate_limit()
                response = self.session.get(url, proxies=proxies_arg)
                
                html = response.text
                if self._is_captcha_page(html):
                    logger.warning("CAPTCHA/consent page detected for query '%s' (proxy=%s)", query, proxy)
                    attempts += 1
                    if attempts >= max_attempts:
                        raise CaptchaDetectedError("Google returned a CAPTCHA challenge; automated access was blocked.")
                    if proxies_arg:
                        logger.warning(
                            "Proxy %s encountered a CAPTCHA challenge. Retrying...",
                            proxy,
                        )
                    else:
                        logger.warning("CAPTCHA challenge detected. Retrying...")

                    self._apply_backoff(attempts)
                    continue

                response.raise_for_status()
                break # Success
            except CaptchaDetectedError:
                raise # Propagate CAPTCHA error immediately
            except requests.RequestException as e:
                attempts += 1
                self._apply_backoff(attempts)
                if proxies_arg:
                    logger.error("Proxy %s failed with error: %s", proxy, e)
                    if attempts >= max_attempts:
                        logger.error("All proxies failed.")
                        return results
                else:
                    logger.error("Error making request: %s", e)
                    return results

        if response is None:
            logger.info("No response received for query '%s'", query)
            return results

        try:
            logger.info("Parsing results for query '%s'", query)
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search result containers
            search_results = soup.find_all('div', class_='g')

            for result in search_results:
                # Extract title
                title_element = result.find('h3')
                title = title_element.get_text() if title_element else "No title"

                # Extract link
                link_element = result.find('a')
                link = link_element.get('href') if link_element else "No link"

                # Extract snippet/description
                snippet_element = result.find('span', class_=['aCOpRe', 'st'])
                if not snippet_element:
                    snippet_element = result.find('div', class_=['VwiC3b', 'yXK7lf'])
                snippet = snippet_element.get_text() if snippet_element else "No description"

                # Only add if we have at least a title and link
                if title != "No title" and link != "No link":
                    results.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet
                    })

                # Stop if we have enough results
                if len(results) >= num_results:
                    break

            # Add delay to be respectful
            time.sleep(self.delay)
            
        except Exception as e:
            logger.exception("Error parsing results: %s", e)

        logger.info("Search complete: query='%s', results=%d", query, len(results))
        return results
    
    def search_and_print(self, query: str, num_results: int = 10) -> None:
        """
        Perform a search and print the results in a formatted way.
        
        Args:
            query: The search query string
            num_results: Number of results to return (default: 10)
        """
        print(f"Searching for: {query}")
        print("=" * 50)
        
        results = self.search(query, num_results)
        
        if not results:
            print("No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   Link: {result['link']}")
            print(f"   Snippet: {result['snippet'][:150]}...")
            print()

    def _is_captcha_page(self, html: Optional[str]) -> bool:
        """Return True when the HTML content contains CAPTCHA or consent markers."""
        if not html:
            return False

        lower_html = html.lower()
        normalized_html = unicodedata.normalize("NFKD", html)
        normalized_lower_html = "".join(
            ch for ch in normalized_html if not unicodedata.combining(ch)
        ).lower()

        search_spaces = (lower_html, normalized_lower_html)

        captcha_indicators = [
            "our systems have detected unusual traffic",
            "to continue, please type the characters",
            "verify that you are not a robot",
            "detected unusual traffic from your computer network",
            "controleer of je geen robot bent",
            "ik ben geen robot",
        ]

        consent_indicators = [
            "consent.google.com",
            "consent.google.nl",
            "before you continue to google search",
            "voordat u doorgaat naar google zoeken",
            "voordat je verdergaat naar google zoeken",
            "avant de continuer vers la recherche google",
            "bevor sie mit der google-suche fortfahren",
        ]

        localized_consent_indicators = [
            "voordat je verdergaat naar google zoeken",
            "ga verder naar google zoeken",
        ]

        recaptcha_markers = [
            "g-recaptcha",
            "grecaptcha",
            "recaptcha/api.js",
        ]

        structural_indicators = [
            '<form action="https://consent.google.com/save"',
            '<form action="https://www.google.com/sorry/index"',
        ]

        indicator_sets = (
            captcha_indicators,
            consent_indicators,
            localized_consent_indicators,
            recaptcha_markers,
            structural_indicators,
        )
        return any(
            any(indicator in space for indicator in indicator_set)
            for indicator_set in indicator_sets
            for space in search_spaces
        )


def main():
    """
    Example usage of the Google scraper.
    """
    scraper = GoogleScraper(delay=1.0)
    
    # Example search
    query = "WBSO subsidie Nederland"
    results = scraper.search(query, num_results=5)
    
    print(f"Found {len(results)} results for '{query}':")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")
        print(f"   {result['snippet'][:100]}...")
        print()


if __name__ == "__main__":
    main()
