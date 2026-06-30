"""RepoContext package initialization."""

from .cli import main

__all__ = ["__version__", "get_version"]

from ._version import __version__, get_version
