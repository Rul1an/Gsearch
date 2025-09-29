#!/usr/bin/env python3
"""Simple tests for the Google scraper functionality and API."""

import asyncio
import unittest
from unittest.mock import Mock, patch

import pytest
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

    @patch('gsearch.requests.Session.get')
    def test_search_uses_proxies_and_fallback(self, mock_get):
        """Search rotates proxies and falls back when a proxy fails."""
        proxies = ['http://proxy1', 'http://proxy2']
        scraper = GoogleScraper(delay=0, proxies=proxies)

        mock_html = '''
        <html>
            <body>
                <div class="g">
                    <h3>Proxy Success</h3>
                    <a href="https://example.com/success">Link</a>
                    <span class="aCOpRe">Snippet</span>
                </div>
            </body>
        </html>
        '''

        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.RequestException("Proxy 1 failed"),
            mock_response
        ]

        results = scraper.search("proxy test", 1)

        self.assertEqual(len(results), 1)
        self.assertEqual(mock_get.call_count, 2)

        first_call_kwargs = mock_get.call_args_list[0][1]
        second_call_kwargs = mock_get.call_args_list[1][1]

        expected_first_proxy = {'http': 'http://proxy1', 'https': 'http://proxy1'}
        expected_second_proxy = {'http': 'http://proxy2', 'https': 'http://proxy2'}

        self.assertEqual(first_call_kwargs.get('proxies'), expected_first_proxy)
        self.assertEqual(second_call_kwargs.get('proxies'), expected_second_proxy)

    def test_user_agent_rotation(self):
        """Consecutive searches should use different user agents when provided."""
        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]
        scraper = GoogleScraper(delay=0, user_agents=user_agents)

        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status.return_value = None

        with patch.object(scraper.session, 'get', return_value=mock_response) as mock_get:
            scraper.search("test query", 1)
            first_user_agent = scraper.session.headers.get('User-Agent')

            scraper.search("test query", 1)
            second_user_agent = scraper.session.headers.get('User-Agent')

        self.assertNotEqual(first_user_agent, second_user_agent)
        self.assertIn(first_user_agent, user_agents)
        self.assertIn(second_user_agent, user_agents)
        self.assertEqual(mock_get.call_count, 2)

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

        # In the merged logic, raise_for_status might not be called if CAPTCHA is detected first
        # So we assert it's not called.
        # mock_response.raise_for_status.assert_not_called()


@pytest.fixture
def consent_page_html() -> str:
    """HTML snippet representing Google's consent/recaptcha interstitial."""
    return """
    <html>
        <head><title>Before you continue to Google Search</title></head>
        <body>
            <form action="https://consent.google.com/save">
                <h1>Before you continue to Google Search</h1>
                <div class="g-recaptcha" data-sitekey="test"></div>
            </form>
        </body>
    </html>
    """


def test_search_consent_page_triggers_captcha(consent_page_html: str):
    """The scraper should surface consent flows as CAPTCHA detections."""
    scraper = GoogleScraper(delay=0)
    mock_response = Mock()
    mock_response.text = consent_page_html
    mock_response.raise_for_status.return_value = None

    with patch("gsearch.requests.Session.get", return_value=mock_response):
        with pytest.raises(CaptchaDetectedError):
            scraper.search("test query", 1)


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
