import subprocess

import pytest


@pytest.mark.parametrize("command", ["full", "export-ai", "export-docs", "changed"])
def test_export_command_help_includes_config_options(command):
    result = subprocess.run(
        ["repocontext", command, "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    help_text = result.stdout
    assert "--config" in help_text
    assert "--no-config" in help_text
    assert ".repocontext.yml" in help_text
