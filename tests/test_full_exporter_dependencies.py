from __future__ import annotations

from pathlib import Path


def test_cli_full_export_write_is_hooked_into_dependency_section() -> None:
    cli_text = Path("src/repocontext/cli.py").read_text(encoding="utf-8")

    assert "append_dependencies_full_section" in cli_text
    assert "_REPOCONTEXT_DEPENDENCY_FULL_EXPORT_HOOK" in cli_text
    assert "_repocontext_add_dependencies_to_full_export(" in cli_text
