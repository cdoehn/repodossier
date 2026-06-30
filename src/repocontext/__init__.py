"""Legacy compatibility namespace for the old repocontext package name.

New code should import repodossier instead.
"""

from importlib import import_module as _import_module

_repodossier = _import_module("repodossier")
__version__ = getattr(_repodossier, "__version__", "0+unknown")


def __getattr__(name):
    return getattr(_repodossier, name)
