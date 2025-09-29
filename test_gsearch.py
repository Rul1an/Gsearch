#!/usr/bin/env python3
"""
Simple tests for the Google scraper functionality.
"""

import unittest
from unittest.mock import Mock, patch

import requests

from gsearch import GoogleScraper


class TestGoogleScraper(unittest.TestCase):
    """Test cases for GoogleScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = GoogleScraper(delay=0)  # No delay for testing
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        self.assertEqual(self.scraper.delay, 0)
        self.assertIsNotNone(self.scraper.session)
        self.assertIn('User-Agent', self.scraper.session.headers)
    
    @patch('gsearch.requests.Session.get')
    def test_search_with_mock_response(self, mock_get):
        """Test search functionality with mocked response."""
        # Mock HTML response
        mock_html = '''
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
        '''
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the search
        results = self.scraper.search("test query", 2)
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Test Title 1')
        self.assertEqual(results[0]['link'], 'https://example.com/1')
        self.assertEqual(results[0]['snippet'], 'Test snippet 1')
    
    @patch('gsearch.requests.Session.get')
    def test_search_empty_results(self, mock_get):
        """Search returns empty list when the network request fails."""
        mock_get.side_effect = requests.RequestException("Network unavailable")

        results = self.scraper.search("test query", 5)

        self.assertEqual(results, [])
        mock_get.assert_called_once()

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


if __name__ == '__main__':
    unittest.main()