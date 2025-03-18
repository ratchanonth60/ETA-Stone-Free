#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import logging
import os
import sys

from django.conf import settings

logger = logging.getLogger(__name__)


def main():
    """Run administrative tasks."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "src.eta.settings"),
    )
    if settings.DEBUG and (
        os.environ.get("RUN_MAIN") or os.environ.get("WERKZEUG_RUN_MAIN")
    ):
        import debugpy

        debugpy.listen((("0.0.0.0", 8080)))
        logger.info("debug redy connect on port: 8080")
        print("Attached remote debugger")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
