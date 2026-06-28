from pathlib import Path
from types import SimpleNamespace

from repocontext.ranking import (
    ImportantFileScore,
    rank_important_files,
)


def make_file(
    relative_path: str,
    *,
    content: str = "",
    is_text: bool | None = True,
    is_binary: bool | None = False,
    error: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        relative_path=Path(relative_path),
        content=content,
        is_text=is_text,
        is_binary=is_binary,
        error=error,
    )


def paths(ranked: tuple[ImportantFileScore, ...]) -> list[str]:
    return [score.path for score in ranked]


def reasons_for(
    ranked: tuple[ImportantFileScore, ...],
    path: str,
) -> tuple[str, ...]:
    by_path = {score.path: score for score in ranked}
    return by_path[path].reasons


def test_rank_important_files_returns_score_model_with_signal_breakdown() -> None:
    ranked = rank_important_files(
        [
            make_file("README.md", content="# Example\n"),
            make_file("src/app.py", content="print('not important yet')\n"),
        ]
    )

    assert ranked
    assert isinstance(ranked[0], ImportantFileScore)

    readme_score = ranked[0]
    assert readme_score.path == "README.md"
    assert readme_score.signals.documentation_score > 0
    assert readme_score.signals.structural_score == 0
    assert readme_score.score == readme_score.signals.total
    assert "Primary project documentation" in readme_score.reasons


def test_documentation_ranking_prioritizes_readme_and_architecture_docs() -> None:
    ranked = rank_important_files(
        [
            make_file("docs/random.md"),
            make_file("docs/architecture.md"),
            make_file("README.md"),
            make_file("src/core.py"),
        ]
    )

    assert paths(ranked) == [
        "README.md",
        "docs/architecture.md",
        "docs/random.md",
    ]

    assert "Architecture documentation" in reasons_for(
        ranked,
        "docs/architecture.md",
    )


def test_structural_ranking_adds_project_configuration_reason() -> None:
    ranked = rank_important_files(
        [
            make_file("pyproject.toml", content="[project]\nname = 'demo'\n"),
            make_file("src/core.py", content="VALUE = 1\n"),
        ]
    )

    assert paths(ranked) == ["pyproject.toml"]
    pyproject_score = ranked[0]
    assert pyproject_score.signals.structural_score > 0
    assert "Python project configuration" in pyproject_score.reasons


def test_generated_exports_binary_files_and_errored_files_are_excluded() -> None:
    ranked = rank_important_files(
        [
            make_file("README.md"),
            make_file("full.txt"),
            make_file("ai.txt"),
            make_file("docs.txt"),
            make_file("changed.txt"),
            make_file("project_bundle.txt"),
            make_file("bundle_project.sh"),
            make_file("docs/binary.md", is_binary=True),
            make_file("docs/unreadable.md", error="permission denied"),
            make_file("docs/non_text.md", is_text=False),
        ]
    )

    assert paths(ranked) == ["README.md"]


def test_tied_scores_sort_deterministically_by_depth_and_path() -> None:
    ranked = rank_important_files(
        [
            make_file("docs/z.md"),
            make_file("docs/a.md"),
        ]
    )

    assert paths(ranked) == ["docs/a.md", "docs/z.md"]


def test_rank_important_files_accepts_plain_paths_and_limit() -> None:
    ranked = rank_important_files(
        [
            Path("README.md"),
            "pyproject.toml",
            "src/app.py",
        ],
        limit=1,
    )

    assert paths(ranked) == ["README.md"]


def test_package_initializer_gets_small_structural_score_without_overranking() -> None:
    ranked = rank_important_files(
        [
            make_file("src/demo/__init__.py", content=""),
            make_file("README.md"),
        ]
    )

    assert paths(ranked) == ["README.md", "src/demo/__init__.py"]

    initializer_score = ranked[1]
    assert initializer_score.signals.structural_score == 5
    assert initializer_score.reasons == ("Package initializer",)
