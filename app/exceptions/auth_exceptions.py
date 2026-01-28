"""Deprecated shim for backwards compatibility.

All exception classes and helpers have been moved to `app.exceptions.errors`.
Import from `app.exceptions` instead.
"""

from app.exceptions.errors import *  # re-export everything for compatibility

