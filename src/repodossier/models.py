"""Data models used by RepoDossier scanning components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = ["FileInfo"]


@dataclass
class FileInfo:
    """Metadata describing a single file encountered during repository scans."""

    relative_path: Path
    absolute_path: Path
    size_bytes: Optional[int] = None
    is_text: Optional[bool] = None
    is_binary: Optional[bool] = None
    language: Optional[str] = None
    line_count: Optional[int] = None
    empty_line_count: Optional[int] = None
    comment_line_count: Optional[int] = None
    estimated_tokens: Optional[int] = None
    content: Optional[str] = None
    error: Optional[str] = None
