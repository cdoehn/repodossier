from pathlib import Path

from repocontext.gitignore import (
    REPOCONTEXT_EXPORT_FILES,
    REPOCONTEXT_GITIGNORE_HEADER,
    ensure_repocontext_gitignore_entries,
)


def test_ensure_repocontext_gitignore_entries_creates_missing_gitignore(
    tmp_path: Path,
) -> None:
    changed = ensure_repocontext_gitignore_entries(tmp_path)

    assert changed is True
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == (
        "# RepoContext exports\n"
        "full.txt\n"
        "ai.txt\n"
        "docs.txt\n"
        "changed.txt\n"
    )


def test_ensure_repocontext_gitignore_entries_preserves_existing_content(
    tmp_path: Path,
) -> None:
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(".venv/\n__pycache__/\n", encoding="utf-8")

    changed = ensure_repocontext_gitignore_entries(tmp_path)

    assert changed is True
    assert gitignore_path.read_text(encoding="utf-8") == (
        ".venv/\n"
        "__pycache__/\n"
        "\n"
        "# RepoContext exports\n"
        "full.txt\n"
        "ai.txt\n"
        "docs.txt\n"
        "changed.txt\n"
    )


def test_ensure_repocontext_gitignore_entries_does_not_duplicate_existing_entries(
    tmp_path: Path,
) -> None:
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("full.txt\n", encoding="utf-8")

    changed = ensure_repocontext_gitignore_entries(tmp_path)

    content = gitignore_path.read_text(encoding="utf-8")
    assert changed is True
    assert content.count("full.txt") == 1
    assert "ai.txt" in content
    assert "docs.txt" in content
    assert "changed.txt" in content


def test_ensure_repocontext_gitignore_entries_completes_existing_block(
    tmp_path: Path,
) -> None:
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(
        "# RepoContext exports\n"
        "full.txt\n",
        encoding="utf-8",
    )

    changed = ensure_repocontext_gitignore_entries(tmp_path)

    assert changed is True
    assert gitignore_path.read_text(encoding="utf-8") == (
        "# RepoContext exports\n"
        "full.txt\n"
        "ai.txt\n"
        "docs.txt\n"
        "changed.txt\n"
    )



def test_repocontext_export_files_include_ai_txt_in_expected_order() -> None:
    assert REPOCONTEXT_EXPORT_FILES == (
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    )


def test_ensure_repocontext_gitignore_entries_adds_missing_ai_txt_to_existing_block(
    tmp_path: Path,
) -> None:
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(
        "# RepoContext exports\n"
        "full.txt\n"
        "docs.txt\n"
        "changed.txt\n",
        encoding="utf-8",
    )

    changed = ensure_repocontext_gitignore_entries(tmp_path)

    content = gitignore_path.read_text(encoding="utf-8")
    export_lines = [
        line
        for line in content.splitlines()
        if line in REPOCONTEXT_EXPORT_FILES
    ]

    assert changed is True
    assert content.count("ai.txt") == 1
    assert set(export_lines) == set(REPOCONTEXT_EXPORT_FILES)
    assert len(export_lines) == len(REPOCONTEXT_EXPORT_FILES)


def test_ensure_repocontext_gitignore_entries_does_not_touch_complete_export_block(
    tmp_path: Path,
) -> None:
    gitignore_path = tmp_path / ".gitignore"
    original_content = (
        "# RepoContext exports\n"
        "full.txt\n"
        "ai.txt\n"
        "docs.txt\n"
        "changed.txt\n"
    )
    gitignore_path.write_text(original_content, encoding="utf-8")

    changed = ensure_repocontext_gitignore_entries(tmp_path)

    assert changed is False
    assert gitignore_path.read_text(encoding="utf-8") == original_content


def test_ensure_repocontext_gitignore_entries_is_idempotent(tmp_path: Path) -> None:
    first_changed = ensure_repocontext_gitignore_entries(tmp_path)
    first_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")

    second_changed = ensure_repocontext_gitignore_entries(tmp_path)
    second_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")

    assert first_changed is True
    assert second_changed is False
    assert second_content == first_content


def test_ensure_repocontext_gitignore_entries_keeps_export_order_stable(
    tmp_path: Path,
) -> None:
    ensure_repocontext_gitignore_entries(tmp_path)

    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    export_lines = [
        line
        for line in lines
        if line in REPOCONTEXT_EXPORT_FILES
    ]

    assert lines[0] == REPOCONTEXT_GITIGNORE_HEADER
    assert export_lines == list(REPOCONTEXT_EXPORT_FILES)
