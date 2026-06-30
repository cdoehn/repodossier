from __future__ import annotations

import inspect
from importlib import import_module
from pathlib import Path

import pytest


LANGUAGE_MODULE = import_module("repocontext.scanner")
DETECTOR_NAME = "detect_language_from_extension"


def _label(value: object) -> str:
    if hasattr(value, "value"):
        value = value.value
    elif hasattr(value, "name"):
        value = value.name
    return str(value).lower()


def _detector_accepts_content() -> bool:
    detector = getattr(LANGUAGE_MODULE, DETECTOR_NAME)
    signature = inspect.signature(detector)

    for name in signature.parameters:
        lowered = name.lower()
        if any(marker in lowered for marker in ("content", "text", "source", "data", "sample", "body")):
            return True

    return False


def _call_detector(path: Path, content: str):
    detector = getattr(LANGUAGE_MODULE, DETECTOR_NAME)
    signature = inspect.signature(detector)

    args = []
    kwargs = {}
    path_sent = False
    content_sent = False

    for name, parameter in signature.parameters.items():
        lowered = name.lower()

        if name == "self":
            continue

        if (
            lowered in {"path", "file_path", "filepath", "relative_path", "absolute_path", "source_path", "filename", "name"}
            or "path" in lowered
            or "file" in lowered
        ):
            kwargs[name] = path
            path_sent = True
            continue

        if any(marker in lowered for marker in ("content", "text", "source", "data", "sample", "body")):
            kwargs[name] = content
            content_sent = True
            continue

        if parameter.default is not inspect._empty:
            continue

        if not path_sent:
            args.append(path)
            path_sent = True
        elif not content_sent:
            args.append(content)
            content_sent = True
        else:
            pytest.skip(f"Cannot call {DETECTOR_NAME} with required parameter {name!r}.")

    return detector(*args, **kwargs)


def test_bash_source_helper_detects_bash_extensions():
    assert LANGUAGE_MODULE.is_bash_source_file(Path("scripts/deploy.sh"))
    assert LANGUAGE_MODULE.is_bash_source_file(Path("scripts/build.bash"))


def test_bash_source_helper_detects_bash_shebangs_without_extension():
    assert LANGUAGE_MODULE.is_bash_source_file(Path("bin/deploy"), "#!/usr/bin/env bash\necho ok\n")
    assert LANGUAGE_MODULE.is_bash_source_file(Path("bin/run"), "#!/bin/bash\necho ok\n")
    assert LANGUAGE_MODULE.is_bash_source_file(Path("bin/run"), "#!/bin/sh\necho ok\n")


def test_bash_source_helper_rejects_non_bash_files():
    assert not LANGUAGE_MODULE.is_bash_source_file(Path("src/app.py"), "print('ok')\n")
    assert not LANGUAGE_MODULE.is_bash_source_file(Path("README.md"), "#!/usr/bin/env python3\n")


def test_language_detector_detects_sh_extension_as_bash_or_shell():
    label = _label(_call_detector(Path("scripts/deploy.sh"), "#!/bin/bash\necho ok\n"))
    assert "bash" in label or "shell" in label or label == "sh"


def test_language_detector_detects_bash_extension_as_bash_or_shell():
    label = _label(_call_detector(Path("scripts/build.bash"), "echo ok\n"))
    assert "bash" in label or "shell" in label or label == "sh"


def test_language_detector_detects_bash_shebang_when_content_is_available():
    if not _detector_accepts_content():
        pytest.skip("The current language detector does not accept file content.")
    label = _label(_call_detector(Path("bin/deploy"), "#!/usr/bin/env bash\necho ok\n"))
    assert "bash" in label or "shell" in label or label == "sh"
