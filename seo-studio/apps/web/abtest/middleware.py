# abtest/middleware.py
import random
from typing import Callable
from django.http import HttpRequest, HttpResponse
from .models import ABTest, TemplatePart

class ABTestMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Attach a dictionary to the request to hold active variants for each slot
        request.active_variants = {}

        # Find all active A/B tests for the user's site
        # This can be optimized by caching
        site = getattr(request, 'site', None) # Assumes a previous middleware sets the site
        if not site:
            return self.get_response(request)

        active_tests = ABTest.objects.filter(
            site=site,
            started_at__isnull=False,
            stopped_at__isnull=True
        )

        for test in active_tests:
            # Check if this user has already been assigned a variant for this test
            cookie_name = f'ab_test_{test.id}'
            assigned_variant_id = request.COOKIES.get(cookie_name)

            if assigned_variant_id:
                try:
                    variant = TemplatePart.objects.get(id=assigned_variant_id)
                    request.active_variants[test.slot] = variant
                    continue
                except TemplatePart.DoesNotExist:
                    # Cookie is stale, re-assign
                    pass

            # If not assigned, choose a variant based on traffic split
            population = list(test.traffic_split.keys())
            weights = list(test.traffic_split.values())

            if not population or sum(weights) == 0:
                continue

            chosen_variant_id = random.choices(population, weights=weights, k=1)[0]

            try:
                variant = TemplatePart.objects.get(id=chosen_variant_id)
                request.active_variants[test.slot] = variant

                # The response needs to set the cookie
                response = self.get_response(request)
                response.set_cookie(cookie_name, str(variant.id), max_age=30*24*60*60) # 30 days
                return response

            except TemplatePart.DoesNotExist:
                continue

        return self.get_response(request)
