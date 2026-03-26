"""Jinja2 email template rendering.

Templates live in src/notifications/templates/ as .html files.
Each template receives a context dict and produces HTML output.

Usage:
    renderer = TemplateRenderer()
    html = renderer.render("adoption_approved", {"adopter_name": "Maria", "animal_name": "Luna"})
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class TemplateRenderer:
    """Renders Jinja2 email templates from the templates directory."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict | None = None) -> str:
        """Render an email template with the given context.

        Args:
            template_name: Template filename without .html extension.
            context: Variables to pass to the template.

        Returns:
            Rendered HTML string.

        Raises:
            TemplateNotFound: If the template file does not exist.
        """
        full_name = f"{template_name}.html"
        try:
            template = self._env.get_template(full_name)
            return template.render(**(context or {}))
        except TemplateNotFound:
            logger.error("Email template not found: %s", full_name)
            raise

    def has_template(self, template_name: str) -> bool:
        """Check whether a template exists."""
        full_name = f"{template_name}.html"
        try:
            self._env.get_template(full_name)
            return True
        except TemplateNotFound:
            return False
