from __future__ import annotations

from pathlib import Path


def test_ai_exporter_is_hooked_into_dependency_section() -> None:
    ai_exporter_text = Path('src/repodossier/exporters/ai.py').read_text(encoding="utf-8")

    assert "append_dependencies_ai_section" in ai_exporter_text
    assert "_REPODOSSIER_DEPENDENCY_AI_EXPORT_WRAPPER" in ai_exporter_text
    assert "_repodossier_wrap_ai_export_function" in ai_exporter_text


def test_ai_exporter_wraps_expected_export_function_names() -> None:
    ai_exporter_text = Path('src/repodossier/exporters/ai.py').read_text(encoding="utf-8")

    for function_name in ('generate_ai_export', 'render_ai_export', 'build_ai_export_context'):
        assert function_name in ai_exporter_text
