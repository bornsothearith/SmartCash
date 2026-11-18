"""Backward-compatible database import.

New code should import ``smartcash.database.connection`` or
``smartcash.database.connect``. This module remains so existing tests and
branches can migrate without breaking their imports.
"""

from smartcash.database.connection import *  # noqa: F401,F403
