from pathlib import Path
from types import SimpleNamespace

from repocontext.call_graph import CallEdge, CallGraph
from repocontext.import_graph import ImportEdge, ImportGraph
from repocontext.ranking import (
    ImportantFileScore,
    rank_important_files,
)
from repocontext.symbols import FileSymbolIndex, SymbolInfo


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


def score_for(
    ranked: tuple[ImportantFileScore, ...],
    path: str,
) -> ImportantFileScore:
    by_path = {score.path: score for score in ranked}
    return by_path[path]


def reasons_for(
    ranked: tuple[ImportantFileScore, ...],
    path: str,
) -> tuple[str, ...]:
    return score_for(ranked, path).reasons


def symbol_index_for_service_project() -> list[FileSymbolIndex]:
    return [
        FileSymbolIndex(
            file_path="src/demo/service.py",
            symbols=[
                SymbolInfo(
                    name="run",
                    kind="function",
                    file_path="src/demo/service.py",
                    line_start=1,
                )
            ],
        )
    ]


def test_rank_important_files_returns_score_model_with_signal_breakdown() -> None:
    ranked = rank_important_files(
        [
            make_file("README.md", content="# Example\n"),
            make_file("src/app.py", content="print('not important yet')\n"),
        ]
    )

    assert ranked
    assert isinstance(ranked[0], ImportantFileScore)

    readme_score = score_for(ranked, "README.md")
    assert readme_score.signals.documentation_score > 0
    assert readme_score.signals.structural_score == 0
    assert readme_score.score == readme_score.signals.total
    assert "Primary project documentation" in readme_score.reasons


def test_pyproject_project_scripts_rank_target_module_as_entrypoint() -> None:
    ranked = rank_important_files(
        [
            make_file(
                "pyproject.toml",
                content="""
[project.scripts]
demo = "demo.cli:main"
""",
            ),
            make_file("src/demo/cli.py", content="def main():\n    pass\n"),
            make_file("src/demo/core.py", content="VALUE = 1\n"),
        ]
    )

    assert paths(ranked)[:2] == ["src/demo/cli.py", "pyproject.toml"]

    cli_score = score_for(ranked, "src/demo/cli.py")
    assert cli_score.signals.entrypoint_score > 0
    assert "Project script entry point" in cli_score.reasons
    assert "Likely Python entry point" in cli_score.reasons


def test_pyproject_poetry_scripts_rank_target_module_as_entrypoint() -> None:
    ranked = rank_important_files(
        [
            make_file(
                "pyproject.toml",
                content="""
[tool.poetry.scripts]
demo = "demo.commands:run"
""",
            ),
            make_file("src/demo/commands.py", content="def run():\n    pass\n"),
            make_file("src/demo/helper.py", content="VALUE = 1\n"),
        ]
    )

    assert "src/demo/commands.py" in paths(ranked)
    command_score = score_for(ranked, "src/demo/commands.py")
    assert command_score.signals.entrypoint_score > 0
    assert command_score.reasons == ("Project script entry point",)


def test_python_main_file_is_ranked_as_module_entrypoint() -> None:
    ranked = rank_important_files(
        [
            make_file("package/__main__.py", content="def main():\n    pass\n"),
            make_file("package/core.py", content="VALUE = 1\n"),
        ]
    )

    assert paths(ranked) == ["package/__main__.py"]
    main_score = ranked[0]
    assert main_score.signals.entrypoint_score > 0
    assert "Python module entry point" in main_score.reasons


def test_classic_python_entrypoint_filenames_are_ranked() -> None:
    ranked = rank_important_files(
        [
            make_file("random_helper.py"),
            make_file("app.py"),
            make_file("main.py"),
            make_file("cli.py"),
        ]
    )

    assert paths(ranked) == ["main.py", "cli.py", "app.py"]
    assert "Likely Python entry point" in reasons_for(ranked, "main.py")
    assert "Likely Python entry point" in reasons_for(ranked, "cli.py")
    assert "Likely Python entry point" in reasons_for(ranked, "app.py")


def test_invalid_pyproject_does_not_crash_entrypoint_detection() -> None:
    ranked = rank_important_files(
        [
            make_file("pyproject.toml", content="[project.scripts\nbroken"),
            make_file("src/demo/cli.py", content="def main():\n    pass\n"),
        ]
    )

    assert paths(ranked) == ["src/demo/cli.py", "pyproject.toml"]
    assert "Likely Python entry point" in reasons_for(ranked, "src/demo/cli.py")


def test_import_centrality_ranks_frequently_imported_file_above_leaf_file() -> None:
    graph = ImportGraph(
        modules={
            "demo.cli": "src/demo/cli.py",
            "demo.api": "src/demo/api.py",
            "demo.worker": "src/demo/worker.py",
            "demo.core": "src/demo/core.py",
            "demo.helper": "src/demo/helper.py",
        },
        edges=[
            ImportEdge(
                source_module="demo.cli",
                target_module="demo.core",
                source_path="src/demo/cli.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
            ImportEdge(
                source_module="demo.api",
                target_module="demo.core",
                source_path="src/demo/api.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
            ImportEdge(
                source_module="demo.worker",
                target_module="demo.core",
                source_path="src/demo/worker.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
        ],
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/cli.py"),
            make_file("src/demo/api.py"),
            make_file("src/demo/worker.py"),
            make_file("src/demo/core.py"),
            make_file("src/demo/helper.py"),
        ],
        import_graph=graph,
    )

    assert paths(ranked)[0] == "src/demo/core.py"
    assert "src/demo/helper.py" not in paths(ranked)

    core_score = score_for(ranked, "src/demo/core.py")
    assert core_score.signals.import_centrality_score > 0
    assert "Imported by 3 local files" in core_score.reasons


def test_import_centrality_gives_small_bonus_to_orchestrating_importers() -> None:
    graph = ImportGraph(
        modules={
            "demo.cli": "src/demo/cli.py",
            "demo.core": "src/demo/core.py",
            "demo.config": "src/demo/config.py",
        },
        edges=[
            ImportEdge(
                source_module="demo.cli",
                target_module="demo.core",
                source_path="src/demo/cli.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
            ImportEdge(
                source_module="demo.cli",
                target_module="demo.config",
                source_path="src/demo/cli.py",
                target_path="src/demo/config.py",
                import_type="from",
                line_number=2,
            ),
        ],
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/cli.py"),
            make_file("src/demo/core.py"),
            make_file("src/demo/config.py"),
        ],
        import_graph=graph,
    )

    cli_score = score_for(ranked, "src/demo/cli.py")
    assert cli_score.signals.import_centrality_score > 0
    assert "Imports 2 local files" in cli_score.reasons


def test_import_centrality_ignores_unknown_graph_nodes() -> None:
    graph = ImportGraph(
        modules={
            "demo.interface": "src/demo/interface.py",
            "demo.core": "src/demo/core.py",
            "demo.ghost": "src/demo/ghost.py",
        },
        edges=[
            ImportEdge(
                source_module="demo.ghost",
                target_module="demo.core",
                source_path="src/demo/ghost.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
            ImportEdge(
                source_module="demo.interface",
                target_module="demo.ghost",
                source_path="src/demo/interface.py",
                target_path="src/demo/ghost.py",
                import_type="from",
                line_number=2,
            ),
        ],
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/interface.py"),
            make_file("src/demo/core.py"),
        ],
        import_graph=graph,
    )

    assert ranked == ()


def test_import_centrality_deduplicates_repeated_edges_by_source_and_target() -> None:
    graph = ImportGraph(
        modules={
            "demo.cli": "src/demo/cli.py",
            "demo.core": "src/demo/core.py",
        },
        edges=[
            ImportEdge(
                source_module="demo.cli",
                target_module="demo.core",
                source_path="src/demo/cli.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=1,
            ),
            ImportEdge(
                source_module="demo.cli",
                target_module="demo.core",
                source_path="src/demo/cli.py",
                target_path="src/demo/core.py",
                import_type="from",
                line_number=2,
            ),
        ],
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/cli.py"),
            make_file("src/demo/core.py"),
        ],
        import_graph=graph,
    )

    core_score = score_for(ranked, "src/demo/core.py")
    assert "Imported by 1 local file" in core_score.reasons


def test_call_centrality_ranks_frequently_called_file_above_unused_file() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/demo/cli.py",
                caller_name="main",
                caller_qualified_name="demo.cli.main",
                callee_name="run",
                callee_qualified_name="demo.service.run",
                line_number=3,
                call_type="function",
                confidence="imported_local",
            ),
            CallEdge(
                caller_file="src/demo/api.py",
                caller_name="handle",
                caller_qualified_name="demo.api.handle",
                callee_name="run",
                callee_qualified_name="demo.service.run",
                line_number=4,
                call_type="function",
                confidence="imported_local",
            ),
            CallEdge(
                caller_file="src/demo/worker.py",
                caller_name="work",
                caller_qualified_name="demo.worker.work",
                callee_name="run",
                callee_qualified_name="demo.service.run",
                line_number=5,
                call_type="function",
                confidence="imported_local",
            ),
        ]
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/cli.py"),
            make_file("src/demo/api.py"),
            make_file("src/demo/worker.py"),
            make_file("src/demo/service.py"),
            make_file("src/demo/unused.py"),
        ],
        call_graph=graph,
        symbols=symbol_index_for_service_project(),
    )

    assert paths(ranked)[0] == "src/demo/service.py"
    assert "src/demo/unused.py" not in paths(ranked)

    service_score = score_for(ranked, "src/demo/service.py")
    assert service_score.signals.call_centrality_score > 0
    assert "Called by 3 local files" in service_score.reasons


def test_call_centrality_gives_small_bonus_to_calling_files() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/demo/controller.py",
                caller_name="handle",
                caller_qualified_name="demo.controller.handle",
                callee_name="run",
                callee_qualified_name="demo.service.run",
                line_number=3,
                call_type="function",
                confidence="imported_local",
            ),
            CallEdge(
                caller_file="src/demo/controller.py",
                caller_name="handle",
                caller_qualified_name="demo.controller.handle",
                callee_name="load",
                callee_qualified_name="demo.config.load",
                line_number=4,
                call_type="function",
                confidence="imported_local",
            ),
        ]
    )

    symbols = [
        FileSymbolIndex(
            file_path="src/demo/service.py",
            symbols=[
                SymbolInfo(
                    name="run",
                    kind="function",
                    file_path="src/demo/service.py",
                    line_start=1,
                )
            ],
        ),
        FileSymbolIndex(
            file_path="src/demo/config.py",
            symbols=[
                SymbolInfo(
                    name="load",
                    kind="function",
                    file_path="src/demo/config.py",
                    line_start=1,
                )
            ],
        ),
    ]

    ranked = rank_important_files(
        [
            make_file("src/demo/controller.py"),
            make_file("src/demo/service.py"),
            make_file("src/demo/config.py"),
        ],
        call_graph=graph,
        symbols=symbols,
    )

    controller_score = score_for(ranked, "src/demo/controller.py")
    assert controller_score.signals.call_centrality_score > 0
    assert "Calls 2 local files" in controller_score.reasons


def test_call_centrality_ignores_unresolved_and_unknown_targets() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/demo/interface.py",
                caller_name="handle",
                caller_qualified_name="demo.interface.handle",
                callee_name="missing",
                callee_qualified_name=None,
                line_number=3,
                call_type="function",
                confidence="unresolved",
            ),
            CallEdge(
                caller_file="src/demo/interface.py",
                caller_name="handle",
                caller_qualified_name="demo.interface.handle",
                callee_name="ghost",
                callee_qualified_name="demo.ghost.run",
                line_number=4,
                call_type="function",
                confidence="imported_local",
            ),
        ]
    )

    ranked = rank_important_files(
        [
            make_file("src/demo/interface.py"),
            make_file("src/demo/core.py"),
        ],
        call_graph=graph,
        symbols=[
            FileSymbolIndex(
                file_path="src/demo/core.py",
                symbols=[
                    SymbolInfo(
                        name="run",
                        kind="function",
                        file_path="src/demo/core.py",
                        line_start=1,
                    )
                ],
            )
        ],
    )

    assert ranked == ()


def test_call_centrality_resolves_methods_through_symbol_parent() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/demo/cli.py",
                caller_name="main",
                caller_qualified_name="demo.cli.main",
                callee_name="execute",
                callee_qualified_name="demo.service.Service.execute",
                line_number=3,
                call_type="method",
                confidence="imported_local",
            )
        ]
    )

    symbols = [
        FileSymbolIndex(
            file_path="src/demo/service.py",
            symbols=[
                SymbolInfo(
                    name="execute",
                    kind="method",
                    file_path="src/demo/service.py",
                    line_start=10,
                    parent="Service",
                )
            ],
        )
    ]

    ranked = rank_important_files(
        [
            make_file("src/demo/cli.py"),
            make_file("src/demo/service.py"),
        ],
        call_graph=graph,
        symbols=symbols,
    )

    service_score = score_for(ranked, "src/demo/service.py")
    assert service_score.signals.call_centrality_score > 0
    assert "Called by 1 local file" in service_score.reasons


def test_call_centrality_handles_empty_call_graph_without_breaking_other_signals() -> None:
    ranked = rank_important_files(
        [
            make_file("README.md"),
            make_file("src/demo/cli.py"),
        ],
        call_graph=CallGraph(),
        symbols=[],
    )

    assert paths(ranked) == ["README.md", "src/demo/cli.py"]


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


def test_python_files_with_milestone_in_name_do_not_get_documentation_score() -> None:
    ranked = rank_important_files(
        [
            make_file(
                "tests/test_call_graph_milestone7_acceptance.py",
                content="def test_acceptance():\n    assert True\n",
            )
        ]
    )

    assert ranked == ()


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


def test_empty_optional_graphs_do_not_break_existing_ranking_signals() -> None:
    ranked = rank_important_files(
        [
            make_file("README.md"),
            make_file("pyproject.toml"),
        ],
        import_graph=None,
        call_graph=None,
    )

    assert paths(ranked) == ["README.md", "pyproject.toml"]
