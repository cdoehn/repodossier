"""RepoDossier package namespace.

This namespace is introduced during the rename from RepoContext to
RepoDossier. The implementation still lives in repocontext until the
package rename commit.
"""

try:
    from repocontext import __version__ as __version__
except ImportError:
    __version__ = "0+unknown"
