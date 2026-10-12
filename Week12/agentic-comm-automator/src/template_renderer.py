# agentic-comm-automator/src/template_renderer.py
import string
from .utils import setup_logging

logger = setup_logging(__name__)

class TemplateRenderer:
    """
    A simple template renderer using Python's str.format syntax, e.g.
    "{report_date}", "{sales_figure:,.2f}" or "{inbox_result[processed_count]}".
    Values come from a context dictionary.
    """
    def __init__(self):
        self._formatter = string.Formatter()

    def render(self, template_string, context):
        """Renders `template_string` with values from `context`. Raises ValueError if a key is missing."""
        if template_string is None:
            return ""
        try:
            return self._formatter.vformat(template_string, [], context)
        except KeyError as e:
            logger.error(f"Missing key in template context: {e}. Template: '{template_string}' "
                         f"Context keys: {sorted(context.keys())}")
            raise ValueError(f"Missing context key: {e}")
        except Exception as e:
            logger.error(f"Error rendering template: {e}. Template: '{template_string}'")
            raise
