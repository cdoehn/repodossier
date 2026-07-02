from repodossier.export_model_compare import (
    FileEntryChange,
    RepositoryExportComparison,
    compare_file_entries,
    compare_repository_exports,
    repository_export_path_delta,
    repository_exports_have_same_paths,
)
from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_content import make_file_entry_from_content


def make_export(*mappings, mode="full", root_name="repo"):
    return repository_export_from_file_mappings(
        mode=mode,
        root_path="/repo",
        root_name=root_name,
        mappings=mappings,
    )


def test_compare_file_entries_reports_changed_fields():
    before = make_file_entry_from_content(
        path="src/app.py",
        language="python",
        content="print(1)\n",
        estimated_tokens=3,
    )
    after = make_file_entry_from_content(
        path="src/app.py",
        language="python",
        content="print(2)\n",
        estimated_tokens=4,
    )

    assert compare_file_entries(before, after) == (
        "estimated_tokens",
        "content",
    )
    assert compare_file_entries(
        before,
        after,
        include_content=False,
    ) == ("estimated_tokens",)


def test_compare_repository_exports_reports_identical_exports():
    before = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        }
    )
    after = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        }
    )

    comparison = compare_repository_exports(before, after)

    assert isinstance(comparison, RepositoryExportComparison)
    assert comparison.same
    assert comparison.same_fingerprint
    assert comparison.added_paths == ()
    assert comparison.removed_paths == ()
    assert comparison.changed_files == ()
    assert comparison.changed_paths() == ()


def test_compare_repository_exports_reports_path_and_content_changes():
    before = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        },
        {
            "path": "old.py",
            "language": "python",
            "content": "old\n",
        },
    )
    after = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(2)\n",
        },
        {
            "path": "new.py",
            "language": "python",
            "content": "new\n",
        },
    )

    comparison = compare_repository_exports(before, after)

    assert not comparison.same
    assert not comparison.same_fingerprint
    assert comparison.added_paths == ("new.py",)
    assert comparison.removed_paths == ("old.py",)
    assert comparison.changed_files == (
        FileEntryChange(path="src/app.py", changed_fields=("content",)),
    )
    assert comparison.changed_paths() == ("new.py", "old.py", "src/app.py")


def test_compare_repository_exports_can_ignore_content_changes():
    before = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        }
    )
    after = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(2)\n",
        }
    )

    comparison = compare_repository_exports(
        before,
        after,
        include_content=False,
    )

    assert comparison.same
    assert comparison.same_fingerprint
    assert comparison.changed_files == ()


def test_compare_repository_exports_reports_mode_and_repository_changes():
    before = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        },
        mode="full",
        root_name="repo",
    )
    after = make_export(
        {
            "path": "src/app.py",
            "language": "python",
            "content": "print(1)\n",
        },
        mode="ai",
        root_name="other-repo",
    )

    comparison = compare_repository_exports(before, after)

    assert not comparison.same
    assert comparison.mode_changed
    assert comparison.repository_changed


def test_repository_export_path_helpers_report_path_delta():
    before = make_export(
        {"path": "a.py", "language": "python"},
        {"path": "b.py", "language": "python"},
    )
    after = make_export(
        {"path": "b.py", "language": "python"},
        {"path": "c.py", "language": "python"},
    )

    assert not repository_exports_have_same_paths(before, after)
    assert repository_export_path_delta(before, after) == (
        ("c.py",),
        ("a.py",),
    )

    assert repository_exports_have_same_paths(before, before)
    assert repository_export_path_delta(before, before) == ((), ())
