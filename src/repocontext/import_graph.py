"""Data models for Python import analysis and dependency graphs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ImportType = Literal["import", "from"]


@dataclass(frozen=True, slots=True)
class ImportReference:
    """A single import statement discovered in a Python source file."""

    source_path: Path
    source_module: str
    imported_module: str | None
    imported_name: str | None = None
    alias: str | None = None
    import_type: ImportType = "import"
    level: int = 0
    line_number: int = 0
    is_relative: bool = False
    is_local: bool | None = None
    resolved_module: str | None = None
    resolved_path: Path | None = None

    def __post_init__(self) -> None:
        if self.import_type not in {"import", "from"}:
            raise ValueError("import_type must be 'import' or 'from'")
        if self.level < 0:
            raise ValueError("level must not be negative")
        if self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))
        if self.resolved_path is not None and not isinstance(self.resolved_path, Path):
            object.__setattr__(self, "resolved_path", Path(self.resolved_path))


@dataclass(frozen=True, slots=True)
class ImportEdge:
    """A local module dependency derived from an import reference."""

    source_module: str
    target_module: str
    source_path: Path
    target_path: Path
    import_type: ImportType
    imported_name: str | None = None
    line_number: int = 0

    def __post_init__(self) -> None:
        if self.import_type not in {"import", "from"}:
            raise ValueError("import_type must be 'import' or 'from'")
        if self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))
        if not isinstance(self.target_path, Path):
            object.__setattr__(self, "target_path", Path(self.target_path))


@dataclass(frozen=True, slots=True)
class ImportAnalysisError:
    """A non-fatal error encountered while analyzing imports in a file."""

    source_path: Path
    message: str
    error_type: str = "ImportAnalysisError"
    line_number: int | None = None

    def __post_init__(self) -> None:
        if self.line_number is not None and self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))


__all__ = [
    "ImportAnalysisError",
    "ImportEdge",
    "ImportReference",
    "ImportType",
]
