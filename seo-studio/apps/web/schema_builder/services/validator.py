# schema_builder/services/validator.py
from typing import List, Dict, Any, Tuple

from content.models import Post
from ..models import SchemaTemplate, SchemaValidationLog

class SchemaValidator:
    def __init__(self, post: Post, template: SchemaTemplate, rendered_jsonld: Dict[str, Any]):
        self.post = post
        self.template = template
        self.rendered_jsonld = rendered_jsonld
        self.errors = []

    def _validate_required_properties(self):
        """Placeholder for schema.org required property validation."""
        schema_type = self.rendered_jsonld.get('@type')
        if not schema_type:
            self.errors.append({"error": "Missing '@type'", "fix": "Ensure the template defines a schema type."})
            return

        # In a real implementation, you would have a map of required properties
        # per schema.org type, e.g., {'Article': ['headline', 'datePublished']}
        required_map = {
            "Article": ["headline", "author", "datePublished"],
            "FAQPage": ["mainEntity"],
        }

        required_props = required_map.get(schema_type, [])
        for prop in required_props:
            if prop not in self.rendered_jsonld:
                self.errors.append({
                    "error": f"Missing required property for {schema_type}: '{prop}'",
                    "fix": f"Ensure the template context provides a value for '{prop}'."
                })

    def _validate_property_formats(self):
        """Placeholder for format validation (e.g., ISO dates, URLs)."""
        if 'datePublished' in self.rendered_jsonld:
            # Basic check, can be improved with regex or date parsing
            if not isinstance(self.rendered_jsonld['datePublished'], str) or 'T' not in self.rendered_jsonld['datePublished']:
                 self.errors.append({"error": "Invalid date format for 'datePublished'", "fix": "Use ISO 8601 format (e.g., YYYY-MM-DDThh:mm:ss)."})


    def validate(self) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Runs all validation checks on the rendered JSON-LD.
        """
        self._validate_required_properties()
        self._validate_property_formats()

        is_valid = len(self.errors) == 0

        # Log the validation result
        SchemaValidationLog.objects.create(
            site=self.post.site,
            post=self.post,
            template=self.template,
            is_valid=is_valid,
            errors=self.errors,
            rendered_jsonld=self.rendered_jsonld
        )

        return is_valid, self.errors

def validate_rendered_schema(post: Post, template: SchemaTemplate, rendered_jsonld: Dict[str, Any]):
    """Convenience function to validate a single rendered schema."""
    validator = SchemaValidator(post, template, rendered_jsonld)
    return validator.validate()
