# robots/services/calculator.py
import re
from urllib.parse import urlparse
from typing import Dict, List, Optional

from core.models import Site
from content.models import Post
from ..models import RobotsGlobal, RobotsRule, MetaRobotsOverride

class EffectiveRobotsCalculator:
    def __init__(self, site: Site):
        self.site = site

    def get_for_url(self, url: str) -> Dict:
        """
        Calculates the effective robots directives for a specific URL.
        """
        parsed_url = urlparse(url)
        path = parsed_url.path

        # 1. Get meta robots override (highest priority)
        post = Post.objects.filter(site=self.site, full_url=url).first()
        meta_override = MetaRobotsOverride.objects.filter(post=post).first()
        if meta_override:
            return {
                "source": "Meta Robots Override",
                "content": meta_override.to_string(),
                "is_allowed": not meta_override.noindex, # Simplified: noindex means disallowed for crawling
            }

        # 2. Check path-specific rules
        rules = RobotsRule.objects.filter(site=self.site)
        matching_rule = None
        for rule in rules:
            if re.match(rule.path_regex, path):
                matching_rule = rule
                break # First match wins (assuming rules are ordered by specificity)

        if matching_rule:
             return {
                "source": "Robots.txt Path Rule",
                "content": f"{'Allow' if matching_rule.is_allowed else 'Disallow'}: {matching_rule.path_regex}",
                "is_allowed": matching_rule.is_allowed,
            }

        # 3. Fallback to global robots.txt content
        global_robots = RobotsGlobal.objects.filter(site=self.site).first()
        return {
            "source": "Global robots.txt",
            "content": global_robots.content if global_robots else "No rules defined.",
            "is_allowed": True, # Default to allowed if no specific rule matches
        }

    def get_robots_txt_content(self) -> str:
        """
        Generates the full content of the robots.txt file.
        """
        global_robots = RobotsGlobal.objects.filter(site=self.site).first()
        base_content = global_robots.content if global_robots else "User-agent: *\nAllow: /"

        path_rules = RobotsRule.objects.filter(site=self.site)

        rules_by_agent = {}
        for rule in path_rules:
            if rule.user_agent not in rules_by_agent:
                rules_by_agent[rule.user_agent] = []
            rules_by_agent[rule.user_agent].append(rule)

        additional_rules = ""
        for agent, rules in rules_by_agent.items():
            additional_rules += f"\\nUser-agent: {agent}\\n"
            for rule in rules:
                rule_type = "Allow" if rule.is_allowed else "Disallow"
                additional_rules += f"{rule_type}: {rule.path_regex}\\n"

        return base_content + "\\n" + additional_rules.strip()


def get_effective_robots_for_url(site_id: str, url: str) -> Optional[Dict]:
    try:
        site = Site.objects.get(id=site_id)
        calculator = EffectiveRobotsCalculator(site)
        return calculator.get_for_url(url)
    except Site.DoesNotExist:
        return None

def get_robots_txt_for_site(site_id: str) -> Optional[str]:
    try:
        site = Site.objects.get(id=site_id)
        calculator = EffectiveRobotsCalculator(site)
        return calculator.get_robots_txt_content()
    except Site.DoesNotExist:
        return None
