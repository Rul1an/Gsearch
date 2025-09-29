#!/usr/bin/env python3
"""
Google Search Scraper for WBSO webcrawler
A simple Python script to scrape Google search results.
"""

import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
from itertools import cycle
from typing import Dict, Iterator, List, Optional, Sequence


class GoogleScraper:
    """
    A simple Google search scraper that extracts search results.
    """
    
    def __init__(self, delay: float = 1.0, user_agents: Optional[Sequence[str]] = None):
        """
        Initialize the Google scraper.

        Args:
            delay: Delay between requests in seconds (default: 1.0)
            user_agents: Optional sequence of user-agent strings to rotate per request.
        """
        self.delay = delay
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.default_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.session.headers.update({'User-Agent': self.default_user_agent})

        filtered_user_agents = [ua for ua in user_agents or [] if ua]
        self._user_agent_iter: Optional[Iterator[str]] = None
        if filtered_user_agents:
            self._user_agent_iter = cycle(filtered_user_agents)
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
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
        
        try:
            # Make the request
            if self._user_agent_iter is not None:
                self.session.headers['User-Agent'] = next(self._user_agent_iter)
            response = self.session.get(url)
            response.raise_for_status()
            
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
            
        except requests.RequestException as e:
            print(f"Error making request: {e}")
        except Exception as e:
            print(f"Error parsing results: {e}")
        
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