"""Configuration loading and validation for RepoContext."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch
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
class FileListLimitResult:
    """Result of applying a max-total-files limit."""

    files: tuple[Any, ...]
    omitted_count: int = 0
    limit: int | None = None



@dataclass(frozen=True)
class ConfiguredFileSelection:
    """Result of applying config filters and file-count limits."""

    files: tuple[Any, ...]
    filtered_count: int = 0
    limit_omitted_count: int = 0
    max_total_files_limit: int | None = None

    @property
    def omitted_count(self) -> int:
        """Total number of files omitted by filters and limits."""

        return self.filtered_count + self.limit_omitted_count

@dataclass(frozen=True)
class RepoContextConfig:
    """Validated RepoContext configuration."""

    include: IncludeExcludeConfig = field(default_factory=IncludeExcludeConfig)
    exclude: IncludeExcludeConfig = field(default_factory=IncludeExcludeConfig)
    limits: ExportLimitsConfig = field(default_factory=ExportLimitsConfig)
    path: Path | None = None
    enabled: bool = False



_ACTIVE_CONFIG: RepoContextConfig | None = None


def set_active_config(config: RepoContextConfig) -> None:
    """Store the active CLI-loaded configuration for downstream scan/export code."""

    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = config


def get_active_config() -> RepoContextConfig:
    """Return the active configuration or built-in defaults."""

    if _ACTIVE_CONFIG is None:
        return RepoContextConfig()
    return _ACTIVE_CONFIG

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

def is_path_included(relative_path: Path | str, config: RepoContextConfig) -> bool:
    """Return whether a repository-relative path is selected by config filters.

    Include rules are additive. If no include rules are configured, a path is
    included by default. Exclude rules always win over include rules.
    """

    candidate = _normalize_filter_path(relative_path)

    include_rules_exist = bool(config.include.paths or config.include.globs)
    if include_rules_exist and not _matches_any_filter(
        candidate,
        config.include.paths,
        config.include.globs,
    ):
        return False

    if _matches_any_filter(candidate, config.exclude.paths, config.exclude.globs):
        return False

    return True


def filter_file_paths(
    relative_paths: list[Path | str] | tuple[Path | str, ...],
    config: RepoContextConfig,
) -> list[Path | str]:
    """Filter repository-relative file paths while preserving input order."""

    return [path for path in relative_paths if is_path_included(path, config)]







def apply_export_byte_limit(rendered: str, config: RepoContextConfig) -> str:
    """Apply max_export_bytes to a rendered export string."""

    limit = config.limits.max_export_bytes
    if limit is None:
        return rendered

    rendered_bytes = rendered.encode("utf-8")
    if len(rendered_bytes) <= limit:
        return rendered

    notice = "\n\n" + format_limit_notice("limits.max_export_bytes was reached") + "\n"
    notice_bytes = notice.encode("utf-8")

    if len(notice_bytes) >= limit:
        return notice_bytes[:limit].decode("utf-8", errors="ignore")

    available_bytes = limit - len(notice_bytes)
    truncated = rendered_bytes[:available_bytes].decode("utf-8", errors="ignore").rstrip()
    return truncated + notice

def add_config_arguments(parser: Any) -> None:
    """Add standard RepoContext configuration CLI arguments to a parser."""

    if not _parser_has_option(parser, "--config"):
        parser.add_argument(
            "--config",
            dest="config_path",
            metavar="PATH",
            help=(
                "Use a specific RepoContext YAML configuration file instead "
                "of the repository-root .repocontext.yml."
            ),
        )

    if not _parser_has_option(parser, "--no-config"):
        parser.add_argument(
            "--no-config",
            action="store_true",
            help="Ignore .repocontext.yml and run with built-in defaults.",
        )



def with_config_arguments(parser: Any) -> Any:
    """Add standard RepoContext configuration CLI arguments and return parser."""

    add_config_arguments(parser)
    return parser

def load_config_from_args(args: Any, start_path: Path | str = ".") -> RepoContextConfig:
    """Load configuration from argparse-style parsed arguments."""

    explicit_config_path = getattr(args, "config_path", None)
    if explicit_config_path is None:
        explicit_config_path = getattr(args, "config", None)

    no_config = bool(getattr(args, "no_config", False))

    if no_config and explicit_config_path:
        raise ConfigError("--config and --no-config cannot be used together.")

    repository_root = discover_repository_root(start_path)
    return load_config(
        repository_root,
        explicit_config_path=explicit_config_path,
        no_config=no_config,
    )


def _parser_has_option(parser: Any, option: str) -> bool:
    for action in getattr(parser, "_actions", []):
        if option in getattr(action, "option_strings", ()):
            return True
    return False

def config_summary_lines(config: RepoContextConfig) -> list[str]:
    """Return stable human-readable summary lines for export metadata."""

    lines = [
        f"Config active: {'yes' if config.enabled else 'no'}",
    ]

    if config.path is not None:
        lines.append(f"Config path: {config.path}")

    lines.extend(
        [
            f"Include paths: {_format_summary_values(config.include.paths)}",
            f"Include globs: {_format_summary_values(config.include.globs)}",
            f"Exclude paths: {_format_summary_values(config.exclude.paths)}",
            f"Exclude globs: {_format_summary_values(config.exclude.globs)}",
            f"Limit max_file_bytes: {_format_summary_limit(config.limits.max_file_bytes)}",
            f"Limit max_total_files: {_format_summary_limit(config.limits.max_total_files)}",
            f"Limit max_export_bytes: {_format_summary_limit(config.limits.max_export_bytes)}",
            f"Limit max_line_count: {_format_summary_limit(config.limits.max_line_count)}",
        ]
    )

    return lines


def format_config_summary(config: RepoContextConfig, heading: str = "Configuration") -> str:
    """Format configuration metadata for text exports."""

    lines = [f"## {heading}", ""]
    lines.extend(f"- {line}" for line in config_summary_lines(config))
    return "\n".join(lines) + "\n"


def _format_summary_values(values: tuple[str, ...]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _format_summary_limit(value: int | None) -> str:
    if value is None:
        return "none"
    return str(value)

def is_file_size_allowed(size_bytes: int | None, config: RepoContextConfig) -> bool:
    """Return whether a file size is allowed by max_file_bytes."""

    limit = config.limits.max_file_bytes
    if limit is None or size_bytes is None:
        return True

    if size_bytes < 0:
        raise ConfigError("size_bytes must not be negative.")

    return size_bytes <= limit


def apply_max_total_files_limit(
    file_infos: list[Any] | tuple[Any, ...],
    config: RepoContextConfig,
) -> FileListLimitResult:
    """Apply max_total_files deterministically while preserving input order."""

    files = tuple(file_infos)
    limit = config.limits.max_total_files
    if limit is None or len(files) <= limit:
        return FileListLimitResult(files=files, omitted_count=0, limit=limit)

    return FileListLimitResult(
        files=files[:limit],
        omitted_count=len(files) - limit,
        limit=limit,
    )


def truncate_text_by_line_limit(
    text: str,
    config: RepoContextConfig,
) -> tuple[str, bool, int]:
    """Return text truncated by max_line_count.

    The tuple contains:
    - resulting text
    - whether truncation happened
    - number of omitted lines
    """

    limit = config.limits.max_line_count
    if limit is None:
        return text, False, 0

    lines = text.splitlines(keepends=True)
    if len(lines) <= limit:
        return text, False, 0

    omitted_count = len(lines) - limit
    return "".join(lines[:limit]), True, omitted_count


def would_exceed_export_byte_limit(
    current_size_bytes: int,
    next_chunk: str | bytes,
    config: RepoContextConfig,
) -> bool:
    """Return whether appending a chunk would exceed max_export_bytes."""

    limit = config.limits.max_export_bytes
    if limit is None:
        return False

    if current_size_bytes < 0:
        raise ConfigError("current_size_bytes must not be negative.")

    if isinstance(next_chunk, str):
        next_size = len(next_chunk.encode("utf-8"))
    else:
        next_size = len(next_chunk)

    return current_size_bytes + next_size > limit


def format_limit_notice(reason: str, *, omitted_count: int | None = None) -> str:
    """Create a stable human-readable export limit notice."""

    suffix = ""
    if omitted_count is not None:
        suffix = f" Omitted: {omitted_count}."
    return f"[RepoContext: content truncated because {reason}.{suffix}]"


def apply_config_to_file_infos(
    file_infos: list[Any] | tuple[Any, ...],
    config: RepoContextConfig,
    repository_root: Path | str | None = None,
) -> ConfiguredFileSelection:
    """Apply include/exclude filters and max_total_files in one stable step."""

    original_files = tuple(file_infos)
    filtered_files = tuple(
        filter_file_infos(
            original_files,
            config,
            repository_root=repository_root,
        )
    )
    limited = apply_max_total_files_limit(filtered_files, config)

    return ConfiguredFileSelection(
        files=limited.files,
        filtered_count=len(original_files) - len(filtered_files),
        limit_omitted_count=limited.omitted_count,
        max_total_files_limit=limited.limit,
    )

def filter_file_infos(
    file_infos: list[Any] | tuple[Any, ...],
    config: RepoContextConfig,
    repository_root: Path | str | None = None,
) -> list[Any]:
    """Filter scanner-style file entries using repository-relative config rules.

    This helper accepts dataclass/object entries or dictionaries. It prefers a
    repository-relative path field and can convert absolute paths when a
    repository root is supplied.
    """

    return [
        file_info
        for file_info in file_infos
        if is_path_included(
            _file_info_filter_path(file_info, repository_root),
            config,
        )
    ]


def _file_info_filter_path(
    file_info: Any,
    repository_root: Path | str | None = None,
) -> str:
    raw_path = _extract_file_info_path(file_info)

    path = Path(raw_path)
    if path.is_absolute() and repository_root is not None:
        try:
            return path.resolve().relative_to(Path(repository_root).resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    return str(raw_path)


def _extract_file_info_path(file_info: Any) -> Path | str:
    if isinstance(file_info, dict):
        for key in ("relative_path", "path", "file_path", "filepath"):
            value = file_info.get(key)
            if value is not None:
                return value

    for attribute in ("relative_path", "path", "file_path", "filepath"):
        value = getattr(file_info, attribute, None)
        if value is not None:
            return value

    raise ConfigError(
        "Cannot apply configuration filters: file entry has no path field."
    )

def _matches_any_filter(
    candidate: str,
    path_rules: tuple[str, ...],
    glob_rules: tuple[str, ...],
) -> bool:
    return any(_matches_path_rule(candidate, rule) for rule in path_rules) or any(
        _matches_glob_rule(candidate, rule) for rule in glob_rules
    )


def _matches_path_rule(candidate: str, rule: str) -> bool:
    normalized_rule = _normalize_filter_path(rule).rstrip("/")
    if not normalized_rule:
        return False

    return candidate == normalized_rule or candidate.startswith(f"{normalized_rule}/")


def _matches_glob_rule(candidate: str, rule: str) -> bool:
    normalized_rule = _normalize_filter_path(rule)
    if not normalized_rule:
        return False

    return fnmatch.fnmatchcase(candidate, normalized_rule)


def _normalize_filter_path(path: Path | str) -> str:
    normalized = str(path).replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")
    return normalized

