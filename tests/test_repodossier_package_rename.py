from pathlib import Path


def test_repodossier_is_the_primary_implementation_package():
    import repodossier
    from repodossier.cli import main

    assert callable(main)
    assert "src/repodossier" in str(Path(repodossier.__path__[0]).as_posix())


def test_repocontext_package_is_only_a_small_legacy_namespace():
    legacy_files = {
        path.relative_to(Path("src/repocontext")).as_posix()
        for path in Path("src/repocontext").rglob("*.py")
    }

    assert legacy_files == {"__init__.py", "__main__.py", "cli.py"}


def test_legacy_repocontext_cli_module_forwards_to_repodossier():
    from repocontext.cli import main as legacy_main
    from repodossier.cli import main as current_main

    assert legacy_main is current_main
