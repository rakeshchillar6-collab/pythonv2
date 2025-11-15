# adminui/services/compliance.py
from django.apps import apps
import inspect

def check_component(app_label, model_name=None, api_path=None, ui_path=None, test_path=None):
    """
    Checks for the existence of key components for a given feature.
    This is a simplified check based on file/class existence.
    """
    report = {
        "implemented": False,
        "tested": False,
        "ui": False,
        "notes": []
    }

    # Check model
    if model_name:
        try:
            apps.get_model(app_label, model_name)
            report["implemented"] = True
        except LookupError:
            report["notes"].append(f"Model {app_label}.{model_name} not found.")

    # Check for tests (simple file existence check)
    if test_path:
        from pathlib import Path
        if Path(test_path).exists():
            report["tested"] = True
        else:
            report["notes"].append(f"Test file not found at {test_path}")

    # In a real app, UI and API checks would be more robust.
    # For now, we'll assume if the model exists, the basics are there.
    if api_path or ui_path:
        report["ui"] = True # Placeholder

    return report

def generate_compliance_report():
    """
    Generates the full validation matrix for all key features.
    """
    report = {
        "Metaphorge": check_component(
            'metaphorge', 'MFProject',
            test_path='seo-studio/apps/web/tests/unit/test_metaphorge.py'
        ),
        "Publishing": check_component(
            'publishing', 'PublishDestination',
            test_path='seo-studio/apps/web/tests/unit/test_publishing.py'
        ),
        "Schema Builder": check_component(
            'schema_builder', 'SchemaTemplate',
            test_path='seo-studio/apps/web/tests/unit/test_schema_builder.py'
        ),
        "RSS Extractor": check_component(
            'rss', 'FeedSource',
            test_path='seo-studio/apps/web/tests/unit/test_rss.py'
        ),
        "Auto-Linking": check_component(
            'autolink', 'LinkRule',
            test_path='seo-studio/apps/web/tests/unit/test_autolink.py'
        ),
        "Vector Search": check_component('vectorsearch', 'Corpus'),
        "Topic Graph": check_component('graph', 'TopicNode'),
        "Content Calendar": check_component('calendar', 'ContentTask'),
    }

    return report
