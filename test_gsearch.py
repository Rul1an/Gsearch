#!/usr/bin/env python3
"""Simple tests for the Google scraper functionality and API."""

import asyncio
import unittest
from unittest.mock import Mock, patch

import requests
from httpx import ASGITransport, AsyncClient

from gsearch import GoogleScraper, CaptchaDetectedError
import app as api_app


class TestGoogleScraper(unittest.TestCase):
    """Test cases for GoogleScraper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = GoogleScraper(delay=0)  # No delay for testing

    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        self.assertEqual(self.scraper.delay, 0)
        self.assertIsNotNone(self.scraper.session)
        self.assertIn("User-Agent", self.scraper.session.headers)

    @patch("gsearch.requests.Session.get")
    def test_search_with_mock_response(self, mock_get):
        """Test search functionality with mocked response."""
        # Mock HTML response
        mock_html = """
        <html>
            <body>
                <div class="g">
                    <h3>Test Title 1</h3>
                    <a href="https://example.com/1">Test Link 1</a>
                    <span class="aCOpRe">Test snippet 1</span>
                </div>
                <div class="g">
                    <h3>Test Title 2</h3>
                    <a href="https://example.com/2">Test Link 2</a>
                    <span class="aCOpRe">Test snippet 2</span>
                </div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the search
        results = self.scraper.search("test query", 2)

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Test Title 1")
        self.assertEqual(results[0]["link"], "https://example.com/1")
        self.assertEqual(results[0]["snippet"], "Test snippet 1")

    @patch("gsearch.requests.Session.get")
    def test_search_empty_results(self, mock_get):
        """Search returns empty list when the network request fails."""
        mock_get.side_effect = requests.RequestException("Network unavailable")

        results = self.scraper.search("test query", 5)

        self.assertEqual(results, [])
        mock_get.assert_called_once()

    @patch("gsearch.requests.Session.get")
    def test_search_captcha_detected_before_http_error(self, mock_get):
        """CAPTCHA detection should occur even when the response is non-2xx."""
        mock_response = Mock()
        mock_response.text = "<html>Our systems have detected unusual traffic from your computer network.</html>"
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = requests.HTTPError("Service Unavailable")
        mock_get.return_value = mock_response

        with self.assertRaises(CaptchaDetectedError):
            self.scraper.search("test query", 1)

        mock_response.raise_for_status.assert_not_called()


class TestAPI(unittest.TestCase):
    """Test cases for the FastAPI layer."""

    @classmethod
    def setUpClass(cls):
        transport = ASGITransport(app=api_app.app)
        cls.client = AsyncClient(transport=transport, base_url="http://testserver")

    @classmethod
    def tearDownClass(cls):
        asyncio.run(cls.client.aclose())

    def test_health_endpoint(self):
        response = asyncio.run(self.client.get("/health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch.object(api_app.scraper, "search", return_value=[
        {"title": "Example", "link": "https://example.com", "snippet": "Snippet"}
    ])
    def test_search_endpoint_uses_scraper(self, mock_search):
        response = asyncio.run(self.client.get("/search", params={"query": "test", "num_results": 1}))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "test")
        self.assertEqual(len(payload["results"]), 1)
        mock_search.assert_called_once_with("test", num_results=1)


if __name__ == "__main__":
    unittest.main()
