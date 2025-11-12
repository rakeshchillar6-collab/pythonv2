# rankme/competitors.py
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List

from textutils import count_words

def fetch_competitor_data(url: str) -> Dict[str, Any]:
    """
    Fetches a competitor's URL and extracts basic SEO metrics.
    - Word count
    - H1-H6 headings

    Returns a dictionary of the extracted data.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main content area if possible (e.g., <main>, <article>, or specific classes)
        # This helps to exclude boilerplate text from word count.
        main_content = soup.find('main') or soup.find('article') or soup.body
        if main_content is None:
            main_content = soup

        # 1. Word Count
        text = main_content.get_text(separator=' ', strip=True)
        word_count = count_words(text)

        # 2. Headings
        headings: Dict[str, List[str]] = {f'h{i}': [] for i in range(1, 7)}
        for i in range(1, 7):
            for header in main_content.find_all(f'h{i}'):
                headings[f'h{i}'].append(header.get_text(strip=True))

        return {
            "word_count": word_count,
            "headings_json": headings,
            "error": None,
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch URL: {e}"}
    except Exception as e:
        return {"error": f"An error occurred during parsing: {e}"}
