# textutils/fa_normalize.py
import re
from django.utils.text import slugify

def normalize_persian_text(text: str) -> str:
    """
    Normalizes a string of Persian text.
    - Replaces Arabic characters with their Persian equivalents.
    - Corrects spacing for punctuation.
    - Collapses multiple whitespace characters.
    """
    if not text:
        return ""

    # Replace Arabic characters with Persian ones
    text = text.replace('ي', 'ی').replace('ك', 'ک')

    # Correct spacing for punctuation (add space after, remove before)
    # This regex adds a space after specified punctuation if it's followed by a letter.
    text = re.sub(r'([.!?؟:؛،])(?=[^\s])', r'\1 ', text)
    # This regex removes space before the specified punctuation.
    text = re.sub(r'\s+([.!?؟:؛،])', r'\1', text)

    # Collapse multiple whitespace characters into a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def slugify_persian(text: str, allow_unicode=True) -> str:
    """
    Creates a clean, URL-friendly slug from a Persian string.
    - Replaces Zero-Width Non-Joiner (ZWNJ) with a space for better word separation.
    - Uses Django's slugify for the main conversion.
    """
    if not text:
        return ""

    # Replace ZWNJ with space to ensure words are separated correctly before slugifying
    text = text.replace('\u200c', ' ')

    return slugify(text, allow_unicode=allow_unicode)
