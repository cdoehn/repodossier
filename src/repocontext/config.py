"""Configuration loading and validation for RepoContext."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import subprocess


CONFIG_FILENAME = ".repocontext.yml"


class ConfigError(ValueError):
    """Raised when a RepoContext configuration file is invalid."""


@dataclass(frozen=True)
class IncludeExcludeConfig:
    """Path and glob based include/exclude rules."""

    paths: tuple[str, ...] = field(default_factory=tuple)
    globs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExportLimitsConfig:
    """Optional export limits loaded from configuration."""

    max_file_bytes: int | None = None
    max_total_files: int | None = None
    max_export_bytes: int | None = None
    max_line_count: int | None = None


@dataclass(frozen=True)
class RepoContextConfig:
    """Validated RepoContext configuration."""

    include: IncludeExcludeConfig = field(default_factory=IncludeExcludeConfig)
    exclude: IncludeExcludeConfig = field(default_factory=IncludeExcludeConfig)
    limits: ExportLimitsConfig = field(default_factory=ExportLimitsConfig)
    path: Path | None = None
    enabled: bool = False


def discover_repository_root(start_path: Path | str = ".") -> Path:
    """Discover the repository root from a file or directory path."""

    start = Path(start_path).resolve()
    current = start.parent if start.is_file() else start

    try:
        result = subprocess.run(
            ["git", "-C", str(current), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        result = None

    if result is not None:
        root = result.stdout.strip()
        if root:
            return Path(root).resolve()

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()

    return current.resolve()


def find_config_path(
    repository_root: Path | str,
    explicit_config_path: Path | str | None = None,
) -> Path | None:
    """Return the active configuration path if one exists."""

    if explicit_config_path is not None:
        path = Path(explicit_config_path).expanduser()
        if not path.is_absolute():
            path = Path(repository_root) / path
        path = path.resolve()
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {path}")
        if not path.is_file():
            raise ConfigError(f"Configuration path is not a file: {path}")
        return path

    path = Path(repository_root).resolve() / CONFIG_FILENAME
    return path if path.is_file() else None


def load_config(
    repository_root: Path | str,
    explicit_config_path: Path | str | None = None,
    *,
    no_config: bool = False,
) -> RepoContextConfig:
    """Load and validate RepoContext configuration for a repository root."""

    if no_config:
        return RepoContextConfig()

    root = Path(repository_root).resolve()
    config_path = find_config_path(root, explicit_config_path)
    if config_path is None:
        return RepoContextConfig()

    data = _read_yaml_mapping(config_path)
    config = parse_config(data)
    return RepoContextConfig(
        include=config.include,
        exclude=config.exclude,
        limits=config.limits,
        path=config_path,
        enabled=True,
    )


def load_config_for_path(
    start_path: Path | str = ".",
    explicit_config_path: Path | str | None = None,
    *,
    no_config: bool = False,
) -> RepoContextConfig:
    """Discover the repository root and load its RepoContext configuration."""

    root = discover_repository_root(start_path)
    return load_config(root, explicit_config_path, no_config=no_config)


def parse_config(data: Any) -> RepoContextConfig:
    """Validate raw YAML data and return a RepoContextConfig."""

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a mapping.")

    allowed_top_level = {"include", "exclude", "limits"}
    unknown_keys = set(data) - allowed_top_level
    if unknown_keys:
        keys = ", ".join(sorted(str(key) for key in unknown_keys))
        raise ConfigError(f"Unknown configuration key(s): {keys}")

    return RepoContextConfig(
        include=_parse_filter_config(data.get("include"), "include"),
        exclude=_parse_filter_config(data.get("exclude"), "exclude"),
        limits=_parse_limits_config(data.get("limits")),
    )


def _read_yaml_mapping(path: Path) -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise ConfigError(
            "PyYAML is required to read .repocontext.yml. "
            "Install RepoContext with its project dependencies."
        ) from exc

    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc


def _parse_filter_config(raw: Any, section_name: str) -> IncludeExcludeConfig:
    if raw is None:
        return IncludeExcludeConfig()

    if not isinstance(raw, dict):
        raise ConfigError(f"{section_name} must be a mapping.")

    allowed_keys = {"paths", "globs"}
    unknown_keys = set(raw) - allowed_keys
    if unknown_keys:
        keys = ", ".join(sorted(str(key) for key in unknown_keys))
        raise ConfigError(f"Unknown {section_name} key(s): {keys}")

    return IncludeExcludeConfig(
        paths=_parse_string_list(raw.get("paths"), f"{section_name}.paths"),
        globs=_parse_string_list(raw.get("globs"), f"{section_name}.globs"),
    )


def _parse_string_list(raw: Any, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()

    if not isinstance(raw, list):
        raise ConfigError(f"{field_name} must be a list of strings.")

    values: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, str):
            raise ConfigError(f"{field_name}[{index}] must be a string.")
        value = item.strip()
        if not value:
            raise ConfigError(f"{field_name}[{index}] must not be empty.")
        values.append(value)

    return tuple(values)


def _parse_limits_config(raw: Any) -> ExportLimitsConfig:
    if raw is None:
        return ExportLimitsConfig()

    if not isinstance(raw, dict):
        raise ConfigError("limits must be a mapping.")

    allowed_keys = {
        "max_file_bytes",
        "max_total_files",
        "max_export_bytes",
        "max_line_count",
    }
    unknown_keys = set(raw) - allowed_keys
    if unknown_keys:
        keys = ", ".join(sorted(str(key) for key in unknown_keys))
        raise ConfigError(f"Unknown limits key(s): {keys}")

    return ExportLimitsConfig(
        max_file_bytes=_parse_optional_positive_int(
            raw.get("max_file_bytes"),
            "limits.max_file_bytes",
        ),
        max_total_files=_parse_optional_positive_int(
            raw.get("max_total_files"),
            "limits.max_total_files",
        ),
        max_export_bytes=_parse_optional_positive_int(
            raw.get("max_export_bytes"),
            "limits.max_export_bytes",
        ),
        max_line_count=_parse_optional_positive_int(
            raw.get("max_line_count"),
            "limits.max_line_count",
        ),
    )


def _parse_optional_positive_int(raw: Any, field_name: str) -> int | None:
    if raw is None:
        return None

    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ConfigError(f"{field_name} must be a positive integer or null.")

    if raw <= 0:
        raise ConfigError(f"{field_name} must be greater than 0.")

    return raw
