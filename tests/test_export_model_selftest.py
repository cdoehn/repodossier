from repodossier.export_model_selftest import (
    ExportModelSelfTestResult,
    assert_export_model_selftest,
    export_model_selftest_lines,
    make_export_model_selftest_export,
    run_export_model_selftest,
)


def test_make_export_model_selftest_export_is_representative():
    export = make_export_model_selftest_export()

    assert export.mode == "full"
    assert export.repository.root_name == "repo"
    assert [entry.path for entry in export.files] == [
        "README.md",
        "src/app.py",
    ]
    assert [entry.path for entry in export.omitted_files] == [
        "assets/logo.png",
    ]
    assert [entry.path for entry in export.truncated_files] == [
        "logs/large.log",
    ]
    assert [warning.code for warning in export.warnings] == [
        "binary",
        "truncated",
    ]


def test_run_export_model_selftest_reports_success():
    result = run_export_model_selftest()

    assert isinstance(result, ExportModelSelfTestResult)
    assert result.valid
    assert result.issues == ()
    assert result.contract_valid is True
    assert result.audit_valid is True
    assert result.readiness_valid is True
    assert result.round_trip_valid is True


def test_assert_export_model_selftest_accepts_current_model():
    assert_export_model_selftest()


def test_export_model_selftest_lines_are_stable():
    assert export_model_selftest_lines() == (
        "valid=True",
        "contract_valid=True",
        "audit_valid=True",
        "readiness_valid=True",
        "round_trip_valid=True",
        "files=2",
        "omitted_files=1",
        "truncated_files=1",
        "warnings=2",
    )
