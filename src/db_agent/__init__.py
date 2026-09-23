"""db-design-agent: AI agent for database schema design from business context."""

from importlib.metadata import version as _version

try:
    __version__ = _version("db-design-agent")
except Exception:
    __version__ = "0.0.0"

__all__ = ["__version__"]
