# textutils/analysis.py
import re
from typing import List
from django.conf import settings

def count_words(text: str) -> int:
    """Counts the number of words in a given text."""
    if not text:
        return 0
    # A simple regex to split by spaces and common punctuation
    words = re.split(r'[\s\.\,\-\(\)\[\]]+', text)
    return len([word for word in words if word])

def calculate_read_time(word_count: int) -> int:
    """
    Calculates the estimated read time in minutes.
    The words-per-minute rate is configurable via Django settings.
    """
    wpm = getattr(settings, 'READING_SPEED_WPM', 180)
    if wpm == 0: return 0

    read_time_minutes = word_count / wpm
    return max(1, round(read_time_minutes))

def calculate_keyword_density(text: str, keyword: str, word_count: int | None = None) -> float:
    """
    Calculates the density of a keyword in a text (case-insensitive).
    Density = (Number of occurrences / Total words) * 100
    """
    if not text or not keyword:
        return 0.0

    total_words = word_count if word_count is not None else count_words(text)
    if total_words == 0:
        return 0.0

    # Count occurrences of the keyword, case-insensitive
    occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))

    density = (occurrences / total_words) * 100
    return round(density, 2)
