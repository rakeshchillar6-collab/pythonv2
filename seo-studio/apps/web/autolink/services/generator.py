# autolink/services/generator.py
import logging
import re
from bs4 import BeautifulSoup

from content.models import Post
from ..models import LinkRule, LinkCandidate

logger = logging.getLogger(__name__)

class CandidateGenerator:
    def __init__(self, rule: LinkRule):
        self.rule = rule
        self.site = rule.site
        self.targets = self._get_targets()

    def _get_targets(self) -> list[Post]:
        """Fetches the pool of posts that can be linked TO."""
        # This can be expanded based on rule.scope
        return list(Post.objects.filter(site=self.site, status=Post.PostStatus.PUBLISHED))

    def _get_sources(self) -> list[Post]:
        """Fetches the pool of posts to scan FOR link opportunities."""
        # In a real app, you might filter for recently updated posts
        return list(Post.objects.filter(site=self.site, status=Post.PostStatus.PUBLISHED))

    def _score_candidate(self, source_post, target_post, anchor) -> float:
        """Scores a potential link. Placeholder logic."""
        # A real scoring function would consider:
        # - Target post's authority (PageRank, RankMe score)
        # - Semantic relevance between source paragraph and target post
        # - Anchor text quality
        return 0.8 # Default high score for now

    def generate(self):
        """Main method to generate link candidates."""
        sources = self._get_sources()

        for source_post in sources:
            soup = BeautifulSoup(source_post.content_html, 'html.parser')

            # Avoid linking inside certain tags
            for excluded_tag in soup.find_all(['h1', 'h2', 'h3', 'a', 'code']):
                excluded_tag.decompose()

            text_content = soup.get_text()

            for target_post in self.targets:
                if source_post.id == target_post.id:
                    continue # Don't link a post to itself

                # Use main keyword as anchor for 'exact' strategy
                anchor_to_find = target_post.main_keyword
                if not anchor_to_find or len(anchor_to_find) < 4:
                    continue

                # Find all occurrences of the anchor text
                for match in re.finditer(re.escape(anchor_to_find), text_content):
                    start, end = match.span()

                    # Basic checks from the rule
                    # This is simplified; real distance check is more complex
                    if source_post.source_candidates.count() >= self.rule.max_links_per_post:
                        break

                    score = self._score_candidate(source_post, target_post, anchor_to_find)
                    context_start = max(0, start - 50)
                    context_end = min(len(text_content), end + 50)

                    LinkCandidate.objects.create(
                        site=self.site,
                        rule=self.rule,
                        source_post=source_post,
                        target_post=target_post,
                        anchor_text=anchor_to_find,
                        start_idx=start,
                        end_idx=end,
                        context_preview=text_content[context_start:context_end],
                        score=score,
                    )

                    # Break after first match if multiple to same target not allowed
                    if not self.rule.allow_multiple_to_same_target:
                        break

def generate_candidates_for_rule(rule_id: str):
    try:
        rule = LinkRule.objects.get(id=rule_id)
        generator = CandidateGenerator(rule)
        generator.generate()
    except LinkRule.DoesNotExist:
        logger.error(f"LinkRule with ID {rule_id} not found.")
