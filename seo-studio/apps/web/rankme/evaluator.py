# rankme/evaluator.py
from typing import List, Dict, Any, TypedDict
from content.models import Post
from textutils import analysis, fa_normalize

class CheckResult(TypedDict):
    id: str
    is_ok: bool
    message: str
    severity: str # 'critical', 'warning', 'info'
    # 'fix' can be added for automated fixes

# --- Individual Check Functions ---

def check_unique_main_keyword(post: Post) -> CheckResult:
    is_unique = not Post.objects.filter(main_keyword__iexact=post.main_keyword, site=post.site).exclude(pk=post.pk).exists()
    return {
        'id': 'unique_main_keyword',
        'is_ok': is_unique,
        'message': 'کلمه کلیدی اصلی باید در کل سایت منحصر به فرد باشد.' if not is_unique else 'کلمه کلیدی اصلی منحصر به فرد است.',
        'severity': 'critical'
    }

def check_h1_contains_keyword(post: Post) -> CheckResult:
    # This is a simplified check. A real implementation would parse the HTML body.
    # For now, we assume H1 is the same as the title.
    contains_keyword = post.main_keyword.lower() in post.title.lower()
    return {
        'id': 'h1_contains_keyword',
        'is_ok': contains_keyword,
        'message': 'عنوان اصلی (H1) باید شامل کلمه کلیدی اصلی باشد.',
        'severity': 'critical'
    }

def check_keyword_in_url(post: Post) -> CheckResult:
    keyword_slug = fa_normalize.slugify_persian(post.main_keyword, allow_unicode=False)
    is_in_url = keyword_slug in post.slug or post.main_keyword in post.title_en.lower().replace(' ', '-')
    return {
        'id': 'keyword_in_url',
        'is_ok': is_in_url,
        'message': 'اسلاگ URL باید شامل کلمه کلیدی اصلی (یا ترجمه انگلیسی آن) باشد.',
        'severity': 'critical'
    }

def check_keyword_density(post: Post, word_count: int) -> CheckResult:
    density = analysis.calculate_keyword_density(post.body_text, post.main_keyword, word_count)
    is_ok = 0.7 <= density <= 1.5
    return {
        'id': 'keyword_density',
        'is_ok': is_ok,
        'message': f'چگالی کلمه کلیدی اصلی {density:.2f}% است. (محدوده ایده‌آل: 0.7-1.5%)',
        'severity': 'warning'
    }

def check_title_pixel_length(post: Post) -> CheckResult:
    # Approximating pixel length with character count
    length = len(post.seo_title or post.title)
    is_ok = 40 <= length <= 60 # Common character limits
    return {
        'id': 'title_length',
        'is_ok': is_ok,
        'message': f'طول عنوان SEO حدود {length} کاراکتر است. (ایده‌آل: 40-60)',
        'severity': 'warning'
    }

def check_meta_description_length(post: Post) -> CheckResult:
    length = len(post.seo_description)
    is_ok = 120 <= length <= 155
    return {
        'id': 'meta_desc_length',
        'is_ok': is_ok,
        'message': f'طول توضیحات متا {length} کاراکتر است. (ایده‌آل: 120-155)',
        'severity': 'warning'
    }

# --- Main Evaluator Function ---

ALL_CHECKS = [
    check_unique_main_keyword,
    check_h1_contains_keyword,
    check_keyword_in_url,
    # Add other checks here...
    # The checks below need word_count, so they are handled inside the main function
]

def evaluate_post(post_id: str) -> Dict[str, Any]:
    """
    Evaluates a Post against a series of SEO rules.

    Returns a dictionary with an overall score and a list of check results.
    """
    try:
        post = Post.objects.prefetch_related('competitors', 'faq_blocks').get(id=post_id)
    except Post.DoesNotExist:
        return {'score': 0, 'checks': [], 'error': 'Post not found.'}

    results: List[CheckResult] = []

    # Pre-calculate values needed by multiple checks
    word_count = analysis.count_words(post.body_text)

    # Run checks that don't need pre-calculated values
    for check_func in ALL_CHECKS:
        results.append(check_func(post))

    # Run checks that need pre-calculated values
    results.append(check_keyword_density(post, word_count))
    results.append(check_title_pixel_length(post))
    results.append(check_meta_description_length(post))

    # TODO: Implement all other checks from the prompt (image alts, read time, etc.)

    # Calculate final score
    passed_checks = sum(1 for r in results if r['is_ok'])
    total_checks = len(results)
    score = (passed_checks / total_checks) * 100 if total_checks > 0 else 100

    return {
        'score': round(score),
        'checks': results,
        'stats': {
            'word_count': word_count,
            'read_time_min': post.read_time_min,
        }
    }
