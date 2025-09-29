#!/usr/bin/env python3
"""
Example usage of the Google scraper for WBSO webcrawler.
"""

from gsearch import GoogleScraper


def main():
    """Demonstrate various ways to use the Google scraper."""
    
    print("Google Scraper Example Usage")
    print("=" * 40)
    
    # Initialize the scraper with a 1-second delay between requests
    scraper = GoogleScraper(delay=1.0)
    
    # Example 1: Basic search
    print("\n1. Basic WBSO-related search:")
    results = scraper.search("WBSO subsidie aanvragen", num_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['title']}")
        print(f"      URL: {result['link']}")
        print(f"      Snippet: {result['snippet'][:100]}...")
        print()
    
    # Example 2: Search with formatted output
    print("\n2. Formatted search output:")
    scraper.search_and_print("RVO WBSO", num_results=3)
    
    # Example 3: Multiple searches for WBSO research
    print("\n3. Multiple WBSO-related searches:")
    queries = [
        "WBSO voorwaarden 2024",
        "WBSO speur- en ontwikkelingswerk",
        "WBSO rapportage verplichtingen"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = scraper.search(query, num_results=2)
        if results:
            print(f"Found {len(results)} results:")
            for result in results[:1]:  # Show only first result
                print(f"  • {result['title']}")
                print(f"    {result['link']}")
        else:
            print("  No results found.")
    
    print("\nExample completed!")


if __name__ == "__main__":
    main()