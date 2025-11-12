# textutils/__init__.py
# This package contains utility functions for text processing and analysis.
from .fa_normalize import normalize_persian_text, slugify_persian
from .analysis import count_words, calculate_read_time, calculate_keyword_density

__all__ = [
    'normalize_persian_text',
    'slugify_persian',
    'count_words',
    'calculate_read_time',
    'calculate_keyword_density',
]
