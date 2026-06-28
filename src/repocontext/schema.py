"""Database schema data model and discovery helpers.

Milestone 11.1 introduces a safe, static foundation for later database schema
extraction. This module does not read table data, does not run migrations, and
does not execute project code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Sequence

from .gitignore import REPOCONTEXT_EXPORT_FILES


SQLITE_SCHEMA_EXTENSIONS: tuple[str, ...] = (
    ".db",
    ".sqlite",
    ".sqlite3",
    ".db3",
    ".s3db",
)

SQL_SCHEMA_FILE_EXTENSIONS: tuple[str, ...] = (
    ".sql",
)

SQL_SCHEMA_DIRECTORIES: tuple[str, ...] = (
    "migrations",
    "schema",
    "sql",
)

SQLITE_MAGIC_HEADER = b"SQLite format 3\x00"


_CREATE_TABLE_PREFIX_RE = re.compile(
    r"^\s*CREATE\s+(?:TEMPORARY\s+|TEMP\s+)?TABLE\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?"
    r"(?P<name>\"(?:\"\"|[^\"])+\"|`[^`]+`|\[[^\]]+\]|[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?)"
    r"\s*\(",
    re.IGNORECASE | re.DOTALL,
)

_COLUMN_STOP_KEYWORDS: frozenset[str] = frozenset(
    {
        "PRIMARY",
        "NOT",
        "NULL",
        "DEFAULT",
        "UNIQUE",
        "CHECK",
        "REFERENCES",
        "COLLATE",
        "GENERATED",
        "AS",
        "CONSTRAINT",
    }
)

_TABLE_CONSTRAINT_KEYWORDS: frozenset[str] = frozenset(
    {
        "CONSTRAINT",
        "PRIMARY",
        "FOREIGN",
        "UNIQUE",
        "CHECK",
        "EXCLUDE",
    }
)


@dataclass(frozen=True, slots=True)
class SchemaColumn:
    """A database table column discovered from schema metadata."""

    name: str
    data_type: str = ""
    nullable: bool | None = None
    default_value: str | None = None
    primary_key_position: int = 0
    position: int | None = None
    raw_definition: str = ""

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        if not cleaned_name:
            raise ValueError("SchemaColumn name must not be empty.")

        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "data_type", self.data_type.strip())
        object.__setattr__(self, "raw_definition", self.raw_definition.strip())

        if self.primary_key_position < 0:
            raise ValueError("primary_key_position must not be negative.")

        if self.position is not None and self.position < 0:
            raise ValueError("position must not be negative.")

    @property
    def is_primary_key(self) -> bool:
        """Return True when this column participates in the primary key."""

        return self.primary_key_position > 0

    def sort_key(self) -> tuple[int, str]:
        """Return a stable sort key for deterministic output.

        Prefer source/schema position when known so rendered schemas keep the
        database's natural column order. Columns without a known position still
        fall back to deterministic name sorting.
        """

        return (
            self.position if self.position is not None else 999_999,
            self.name,
        )


@dataclass(frozen=True, slots=True)
class SchemaForeignKey:
    """A foreign key relationship between two tables."""

    table: str
    from_column: str
    to_table: str
    to_column: str
    on_update: str = ""
    on_delete: str = ""
    match: str = ""

    def __post_init__(self) -> None:
        for field_name in ("table", "from_column", "to_table", "to_column"):
            value = getattr(self, field_name).strip()
            if not value:
                raise ValueError(f"SchemaForeignKey {field_name} must not be empty.")
            object.__setattr__(self, field_name, value)

        object.__setattr__(self, "on_update", self.on_update.strip())
        object.__setattr__(self, "on_delete", self.on_delete.strip())
        object.__setattr__(self, "match", self.match.strip())

    def sort_key(self) -> tuple[str, str, str, str]:
        """Return a stable sort key for deterministic output."""

        return (self.table, self.from_column, self.to_table, self.to_column)


@dataclass(frozen=True, slots=True)
class SchemaIndex:
    """A database index discovered from schema metadata."""

    name: str
    table: str
    unique: bool = False
    columns: tuple[str, ...] = field(default_factory=tuple)
    origin: str = ""
    partial: bool = False

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        cleaned_table = self.table.strip()
        if not cleaned_name:
            raise ValueError("SchemaIndex name must not be empty.")
        if not cleaned_table:
            raise ValueError("SchemaIndex table must not be empty.")

        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "table", cleaned_table)
        object.__setattr__(
            self,
            "columns",
            tuple(str(column).strip() for column in self.columns if str(column).strip()),
        )
        object.__setattr__(self, "origin", self.origin.strip())

    def sort_key(self) -> tuple[str, str]:
        """Return a stable sort key for deterministic output."""

        return (self.table, self.name)


@dataclass(frozen=True, slots=True)
class SchemaTable:
    """A table, view, or virtual table discovered from a database schema."""

    name: str
    table_type: str = "table"
    columns: tuple[SchemaColumn, ...] = field(default_factory=tuple)
    foreign_keys: tuple[SchemaForeignKey, ...] = field(default_factory=tuple)
    indexes: tuple[SchemaIndex, ...] = field(default_factory=tuple)
    create_sql: str = ""
    source_file: str = ""

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        cleaned_table_type = self.table_type.strip().lower() or "unknown"

        if not cleaned_name:
            raise ValueError("SchemaTable name must not be empty.")

        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "table_type", cleaned_table_type)
        object.__setattr__(
            self,
            "columns",
            tuple(sorted(self.columns, key=lambda column: column.sort_key())),
        )
        object.__setattr__(
            self,
            "foreign_keys",
            tuple(sorted(self.foreign_keys, key=lambda key: key.sort_key())),
        )
        object.__setattr__(
            self,
            "indexes",
            tuple(sorted(self.indexes, key=lambda index: index.sort_key())),
        )
        object.__setattr__(self, "create_sql", self.create_sql.strip())
        object.__setattr__(self, "source_file", Path(self.source_file).as_posix() if self.source_file else "")

    def sort_key(self) -> tuple[str, str, str]:
        """Return a stable sort key for deterministic output."""

        return (self.source_file, self.table_type, self.name)


@dataclass(frozen=True, slots=True)
class DatabaseSchemaReport:
    """Collected database schema discovery and extraction result."""

    database_files: tuple[str, ...] = field(default_factory=tuple)
    tables: tuple[SchemaTable, ...] = field(default_factory=tuple)
    views: tuple[SchemaTable, ...] = field(default_factory=tuple)
    sql_schema_files: tuple[str, ...] = field(default_factory=tuple)
    create_statements: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    unsupported_files: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "database_files", _unique_sorted_posix(self.database_files))
        object.__setattr__(self, "sql_schema_files", _unique_sorted_posix(self.sql_schema_files))
        object.__setattr__(self, "unsupported_files", _unique_sorted_posix(self.unsupported_files))
        object.__setattr__(self, "tables", tuple(sorted(self.tables, key=lambda table: table.sort_key())))
        object.__setattr__(self, "views", tuple(sorted(self.views, key=lambda table: table.sort_key())))
        object.__setattr__(self, "create_statements", tuple(str(item) for item in self.create_statements))
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(self, "errors", tuple(str(item) for item in self.errors))

    def is_empty(self) -> bool:
        """Return True when no schema-related files or schema objects were found."""

        return (
            not self.database_files
            and not self.sql_schema_files
            and not self.tables
            and not self.views
            and not self.unsupported_files
        )


def is_generated_export_file(path: str | Path) -> bool:
    """Return True when path is a generated RepoContext export file."""

    return Path(path).name in REPOCONTEXT_EXPORT_FILES


def is_sqlite_candidate_path(path: str | Path) -> bool:
    """Return True when a path name looks like a SQLite database file."""

    path_obj = Path(path)
    if is_generated_export_file(path_obj):
        return False
    return path_obj.suffix.lower() in SQLITE_SCHEMA_EXTENSIONS


def is_sql_schema_candidate_path(path: str | Path) -> bool:
    """Return True when a path name looks like a SQL schema source file."""

    path_obj = Path(path)
    if is_generated_export_file(path_obj):
        return False

    parts_lower = tuple(part.lower() for part in path_obj.parts)

    if path_obj.suffix.lower() in SQL_SCHEMA_FILE_EXTENSIONS:
        return True

    return any(part in SQL_SCHEMA_DIRECTORIES for part in parts_lower)


def has_sqlite_magic_header(path: str | Path) -> bool:
    """Return True when a file starts with the SQLite 3 magic header."""

    try:
        with Path(path).open("rb") as handle:
            return handle.read(len(SQLITE_MAGIC_HEADER)) == SQLITE_MAGIC_HEADER
    except OSError:
        return False


def discover_database_schema_files(
    repo_root: str | Path,
    files: Iterable[object] | None = None,
    *,
    allow_filesystem_scan: bool = False,
) -> DatabaseSchemaReport:
    """Discover SQLite and SQL schema files.

    When ``files`` is provided, only those file references are considered. This
    is the preferred export-pipeline mode because callers can pass Git-tracked
    scanner results.

    When ``files`` is omitted, discovery does not scan the filesystem by
    default. This protects RepoContext's Git-tracked-only contract. Tests or
    diagnostic callers may opt into a raw filesystem scan with
    ``allow_filesystem_scan=True``.
    """

    root = Path(repo_root)
    database_files: list[str] = []
    sql_schema_files: list[str] = []
    unsupported_files: list[str] = []
    warnings: list[str] = []

    for candidate_path in _iter_discovery_paths(
        root,
        files,
        allow_filesystem_scan=allow_filesystem_scan,
    ):
        relative_path = _relative_path(root, candidate_path)

        if is_generated_export_file(relative_path):
            continue

        if is_sqlite_candidate_path(relative_path):
            if has_sqlite_magic_header(candidate_path):
                database_files.append(relative_path)
            else:
                unsupported_files.append(relative_path)
                warnings.append(f"{relative_path}: file extension suggests SQLite but magic header is missing")
            continue

        if is_sql_schema_candidate_path(relative_path):
            sql_schema_files.append(relative_path)

    return DatabaseSchemaReport(
        database_files=tuple(database_files),
        sql_schema_files=tuple(sql_schema_files),
        warnings=tuple(warnings),
        unsupported_files=tuple(unsupported_files),
    )


def _iter_discovery_paths(
    repo_root: Path,
    files: Iterable[object] | None,
    *,
    allow_filesystem_scan: bool = False,
) -> tuple[Path, ...]:
    """Return absolute candidate paths in stable order."""

    paths: list[Path] = []

    if files is None:
        if not allow_filesystem_scan:
            return ()

        for path in sorted(repo_root.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_file():
                paths.append(path)
    else:
        for file_item in files:
            path = _coerce_file_path(file_item)
            if path is None:
                continue

            absolute_path = path if path.is_absolute() else repo_root / path
            if absolute_path.exists() and absolute_path.is_file():
                paths.append(absolute_path)

    return tuple(dict.fromkeys(path.resolve() for path in paths))


def _coerce_file_path(file_item: object) -> Path | None:
    """Return a Path from path-like objects or FileInfo-like objects."""

    if isinstance(file_item, Path):
        return file_item

    if isinstance(file_item, str):
        return Path(file_item)

    for attribute_name in ("absolute_path", "relative_path", "path", "name"):
        attribute_value = getattr(file_item, attribute_name, None)
        if isinstance(attribute_value, Path):
            return attribute_value
        if isinstance(attribute_value, str):
            return Path(attribute_value)

    return None


def _relative_path(repo_root: Path, path: Path) -> str:
    """Return a stable repository-relative POSIX path when possible."""

    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _unique_sorted_posix(values: Sequence[str | Path]) -> tuple[str, ...]:
    """Return unique POSIX path strings sorted deterministically."""

    return tuple(sorted({Path(value).as_posix() for value in values}))


def extract_sqlite_schema_file(
    database_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> DatabaseSchemaReport:
    """Extract schema metadata from one SQLite database file.

    The database is opened read-only. Only SQLite schema metadata and PRAGMA
    metadata are queried; table contents are never selected or exported.
    """

    path = Path(database_path)
    root = Path(repo_root) if repo_root is not None else path.parent
    source_file = _relative_path(root, path)

    if not has_sqlite_magic_header(path):
        return DatabaseSchemaReport(
            unsupported_files=(source_file,),
            warnings=(f"{source_file}: file extension suggests SQLite but magic header is missing",),
        )

    try:
        connection = _connect_sqlite_readonly(path)
    except (OSError, sqlite3.Error) as exc:
        return DatabaseSchemaReport(
            database_files=(source_file,),
            warnings=(f"{source_file}: could not open SQLite database read-only: {type(exc).__name__}: {exc}",),
        )

    try:
        tables, views, warnings = _extract_sqlite_schema_from_connection(
            connection,
            source_file=source_file,
        )
    except sqlite3.Error as exc:
        return DatabaseSchemaReport(
            database_files=(source_file,),
            warnings=(f"{source_file}: could not read SQLite schema: {type(exc).__name__}: {exc}",),
        )
    finally:
        connection.close()

    return DatabaseSchemaReport(
        database_files=(source_file,),
        tables=tuple(tables),
        views=tuple(views),
        warnings=tuple(warnings),
    )


def _connect_sqlite_readonly(path: Path) -> sqlite3.Connection:
    """Open a SQLite database in read-only URI mode."""

    uri = path.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _extract_sqlite_schema_from_connection(
    connection: sqlite3.Connection,
    *,
    source_file: str,
) -> tuple[list[SchemaTable], list[SchemaTable], list[str]]:
    """Return tables, views, and warnings from an open SQLite connection."""

    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE type IN ('table', 'view')
        ORDER BY type, name
        """
    ).fetchall()

    tables: list[SchemaTable] = []
    views: list[SchemaTable] = []
    warnings: list[str] = []

    for schema_type, name, table_name, create_sql in rows:
        object_name = str(name or table_name or "").strip()
        if not object_name:
            warnings.append(f"{source_file}: skipped SQLite schema object without a name")
            continue

        if _is_internal_sqlite_object(object_name):
            continue

        normalized_create_sql = str(create_sql or "").strip()
        table_type = _sqlite_table_type(schema_type, normalized_create_sql)

        try:
            columns = _read_sqlite_columns(connection, object_name)
            foreign_keys = _read_sqlite_foreign_keys(connection, object_name)
            indexes = _read_sqlite_indexes(connection, object_name)
        except sqlite3.Error as exc:
            warnings.append(
                f"{source_file}: could not read metadata for {object_name}: "
                f"{type(exc).__name__}: {exc}"
            )
            columns = ()
            foreign_keys = ()
            indexes = ()

        schema_table = SchemaTable(
            name=object_name,
            table_type=table_type,
            columns=columns,
            foreign_keys=foreign_keys,
            indexes=indexes,
            create_sql=normalized_create_sql,
            source_file=source_file,
        )

        if table_type == "view":
            views.append(schema_table)
        else:
            tables.append(schema_table)

    return tables, views, warnings


def _sqlite_table_type(schema_type: object, create_sql: str) -> str:
    """Return RepoContext's normalized table type for a SQLite schema object."""

    schema_type_text = str(schema_type or "").strip().lower()

    if schema_type_text == "view":
        return "view"

    if create_sql.lstrip().upper().startswith("CREATE VIRTUAL TABLE"):
        return "virtual_table"

    if schema_type_text == "table":
        return "table"

    return "unknown"


def _is_internal_sqlite_object(name: str) -> bool:
    """Return True for SQLite's internal bookkeeping tables and indexes."""

    return name.lower().startswith("sqlite_")


def _quote_sqlite_identifier(identifier: str) -> str:
    """Return a safely quoted SQLite identifier for PRAGMA calls."""

    return '"' + identifier.replace('"', '""') + '"'


def _read_sqlite_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[SchemaColumn, ...]:
    """Read column metadata for one SQLite table or view."""

    rows = connection.execute(
        f"PRAGMA table_info({_quote_sqlite_identifier(table_name)})"
    ).fetchall()

    columns: list[SchemaColumn] = []
    for row in rows:
        # PRAGMA table_info columns:
        # cid, name, type, notnull, dflt_value, pk
        name = _clean_schema_value(row[1])
        if not name:
            continue

        data_type = _clean_schema_value(row[2])
        nullable = not bool(row[3])
        default_value = None if row[4] is None else str(row[4])
        primary_key_position = int(row[5] or 0)

        columns.append(
            SchemaColumn(
                name=name,
                data_type=data_type,
                nullable=nullable,
                default_value=default_value,
                primary_key_position=primary_key_position,
                position=int(row[0] or 0),
            )
        )

    return tuple(columns)


def _read_sqlite_foreign_keys(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[SchemaForeignKey, ...]:
    """Read foreign-key metadata for one SQLite table."""

    rows = connection.execute(
        f"PRAGMA foreign_key_list({_quote_sqlite_identifier(table_name)})"
    ).fetchall()

    foreign_keys: list[SchemaForeignKey] = []
    for row in rows:
        # PRAGMA foreign_key_list columns:
        # id, seq, table, from, to, on_update, on_delete, match
        foreign_keys.append(
            SchemaForeignKey(
                table=table_name,
                from_column=_clean_schema_value(row[3], default="unknown"),
                to_table=_clean_schema_value(row[2], default="unknown"),
                to_column=_clean_schema_value(row[4], default="unknown"),
                on_update=_clean_schema_value(row[5]),
                on_delete=_clean_schema_value(row[6]),
                match=_clean_schema_value(row[7]),
            )
        )

    return tuple(foreign_keys)


def _read_sqlite_indexes(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[SchemaIndex, ...]:
    """Read non-internal index metadata for one SQLite table."""

    rows = connection.execute(
        f"PRAGMA index_list({_quote_sqlite_identifier(table_name)})"
    ).fetchall()

    indexes: list[SchemaIndex] = []
    for row in rows:
        # PRAGMA index_list columns:
        # seq, name, unique, origin, partial
        index_name = _clean_schema_value(row[1])
        if not index_name or _is_internal_sqlite_object(index_name):
            continue

        columns = _read_sqlite_index_columns(connection, index_name)
        indexes.append(
            SchemaIndex(
                name=index_name,
                table=table_name,
                unique=bool(row[2]),
                columns=columns,
                origin=_clean_schema_value(row[3]),
                partial=bool(row[4]),
            )
        )

    return tuple(indexes)


def _read_sqlite_index_columns(
    connection: sqlite3.Connection,
    index_name: str,
) -> tuple[str, ...]:
    """Read indexed column names for one SQLite index."""

    rows = connection.execute(
        f"PRAGMA index_info({_quote_sqlite_identifier(index_name)})"
    ).fetchall()

    columns: list[str] = []
    for row in rows:
        # PRAGMA index_info columns:
        # seqno, cid, name
        column_name = _clean_schema_value(row[2])
        if column_name:
            columns.append(column_name)

    return tuple(columns)


def _clean_schema_value(value: object, *, default: str = "") -> str:
    """Return a compact string value for schema metadata."""

    if value is None:
        return default
    text = str(value).strip()
    return text or default


def extract_sql_schema_file(
    sql_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    encoding: str = "utf-8",
) -> DatabaseSchemaReport:
    """Extract best-effort CREATE TABLE schema metadata from one SQL file.

    This is intentionally not a full SQL parser. It recognizes common CREATE
    TABLE statements and extracts a useful, conservative table/column summary.
    Project code and migrations are never executed.
    """

    path = Path(sql_path)
    root = Path(repo_root) if repo_root is not None else path.parent
    source_file = _relative_path(root, path)

    try:
        sql_text = path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError) as exc:
        return DatabaseSchemaReport(
            sql_schema_files=(source_file,),
            warnings=(f"{source_file}: could not read SQL schema file: {type(exc).__name__}: {exc}",),
        )

    create_statements = extract_create_table_statements_from_sql(sql_text)
    tables: list[SchemaTable] = []
    warnings: list[str] = []

    for statement in create_statements:
        table = parse_create_table_statement(statement, source_file=source_file)
        if table is None:
            warnings.append(f"{source_file}: could not parse CREATE TABLE statement")
            continue
        tables.append(table)

    if not create_statements:
        warnings.append(f"{source_file}: no CREATE TABLE statements found")

    return DatabaseSchemaReport(
        sql_schema_files=(source_file,),
        tables=tuple(tables),
        create_statements=create_statements,
        warnings=tuple(warnings),
    )


def extract_create_table_statements_from_sql(sql_text: str) -> tuple[str, ...]:
    """Return CREATE TABLE statements from SQL text in deterministic order."""

    statements = _split_sql_statements(sql_text)
    return tuple(
        statement
        for statement in statements
        if _CREATE_TABLE_PREFIX_RE.match(statement)
    )


def parse_create_table_statement(
    statement: str,
    *,
    source_file: str = "",
) -> SchemaTable | None:
    """Parse a single CREATE TABLE statement into a SchemaTable if possible."""

    cleaned_statement = statement.strip().rstrip(";").strip()
    match = _CREATE_TABLE_PREFIX_RE.match(cleaned_statement)
    if match is None:
        return None

    table_name = _normalize_sql_identifier(match.group("name"))
    if not table_name:
        return None

    body = _extract_parenthesized_body(cleaned_statement, match.end() - 1)
    if body is None:
        return SchemaTable(
            name=table_name,
            table_type="table",
            create_sql=cleaned_statement,
            source_file=source_file,
        )

    columns: list[SchemaColumn] = []
    foreign_keys: list[SchemaForeignKey] = []
    column_position = 0

    for item in _split_top_level_comma_items(body):
        if not item:
            continue

        leading_keyword = _leading_sql_keyword(item)
        if leading_keyword in _TABLE_CONSTRAINT_KEYWORDS:
            foreign_key = _parse_foreign_key_constraint(item, table_name)
            if foreign_key is not None:
                foreign_keys.append(foreign_key)
            continue

        column = _parse_create_table_column(item, position=column_position)
        if column is not None:
            columns.append(column)
            column_position += 1

    return SchemaTable(
        name=table_name,
        table_type="table",
        columns=tuple(columns),
        foreign_keys=tuple(foreign_keys),
        create_sql=cleaned_statement,
        source_file=source_file,
    )


def _split_sql_statements(sql_text: str) -> tuple[str, ...]:
    """Split SQL text into statements while respecting quotes and comments."""

    statements: list[str] = []
    current: list[str] = []

    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_bracket = False
    in_line_comment = False
    in_block_comment = False
    paren_depth = 0
    index = 0

    while index < len(sql_text):
        char = sql_text[index]
        next_char = sql_text[index + 1] if index + 1 < len(sql_text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                current.append(char)
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue

        if not (in_single_quote or in_double_quote or in_backtick or in_bracket):
            if char == "-" and next_char == "-":
                in_line_comment = True
                index += 2
                continue
            if char == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue

        current.append(char)

        if in_single_quote:
            if char == "'" and next_char == "'":
                current.append(next_char)
                index += 2
                continue
            if char == "'":
                in_single_quote = False
            index += 1
            continue

        if in_double_quote:
            if char == '"' and next_char == '"':
                current.append(next_char)
                index += 2
                continue
            if char == '"':
                in_double_quote = False
            index += 1
            continue

        if in_backtick:
            if char == "`":
                in_backtick = False
            index += 1
            continue

        if in_bracket:
            if char == "]":
                in_bracket = False
            index += 1
            continue

        if char == "'":
            in_single_quote = True
        elif char == '"':
            in_double_quote = True
        elif char == "`":
            in_backtick = True
        elif char == "[":
            in_bracket = True
        elif char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == ";" and paren_depth == 0:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

        index += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return tuple(statements)


def _extract_parenthesized_body(statement: str, open_paren_index: int) -> str | None:
    """Return text inside the parenthesized CREATE TABLE body."""

    if open_paren_index < 0 or open_paren_index >= len(statement):
        return None
    if statement[open_paren_index] != "(":
        return None

    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_bracket = False
    depth = 0
    body_start = open_paren_index + 1
    index = open_paren_index

    while index < len(statement):
        char = statement[index]
        next_char = statement[index + 1] if index + 1 < len(statement) else ""

        if in_single_quote:
            if char == "'" and next_char == "'":
                index += 2
                continue
            if char == "'":
                in_single_quote = False
            index += 1
            continue

        if in_double_quote:
            if char == '"' and next_char == '"':
                index += 2
                continue
            if char == '"':
                in_double_quote = False
            index += 1
            continue

        if in_backtick:
            if char == "`":
                in_backtick = False
            index += 1
            continue

        if in_bracket:
            if char == "]":
                in_bracket = False
            index += 1
            continue

        if char == "'":
            in_single_quote = True
        elif char == '"':
            in_double_quote = True
        elif char == "`":
            in_backtick = True
        elif char == "[":
            in_bracket = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return statement[body_start:index]

        index += 1

    return None


def _split_top_level_comma_items(text: str) -> tuple[str, ...]:
    """Split comma-separated SQL fragments while respecting nested syntax."""

    items: list[str] = []
    current: list[str] = []

    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_bracket = False
    depth = 0
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        current.append(char)

        if in_single_quote:
            if char == "'" and next_char == "'":
                current.append(next_char)
                index += 2
                continue
            if char == "'":
                in_single_quote = False
            index += 1
            continue

        if in_double_quote:
            if char == '"' and next_char == '"':
                current.append(next_char)
                index += 2
                continue
            if char == '"':
                in_double_quote = False
            index += 1
            continue

        if in_backtick:
            if char == "`":
                in_backtick = False
            index += 1
            continue

        if in_bracket:
            if char == "]":
                in_bracket = False
            index += 1
            continue

        if char == "'":
            in_single_quote = True
        elif char == '"':
            in_double_quote = True
        elif char == "`":
            in_backtick = True
        elif char == "[":
            in_bracket = True
        elif char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        elif char == "," and depth == 0:
            item = "".join(current[:-1]).strip()
            if item:
                items.append(item)
            current = []

        index += 1

    tail = "".join(current).strip()
    if tail:
        items.append(tail)

    return tuple(items)


def _parse_create_table_column(
    definition: str,
    *,
    position: int | None = None,
) -> SchemaColumn | None:
    """Parse one best-effort CREATE TABLE column definition."""

    column_name, remainder = _read_sql_identifier(definition)
    if not column_name:
        return None

    upper_remainder = remainder.upper()
    data_type = _extract_column_data_type(remainder)
    nullable = None

    if re.search(r"\bNOT\s+NULL\b", upper_remainder):
        nullable = False
    elif re.search(r"\bNULL\b", upper_remainder):
        nullable = True

    primary_key_position = 1 if re.search(r"\bPRIMARY\s+KEY\b", upper_remainder) else 0

    return SchemaColumn(
        name=column_name,
        data_type=data_type,
        nullable=nullable,
        default_value=_extract_default_value(remainder),
        primary_key_position=primary_key_position,
        position=position,
        raw_definition=definition,
    )


def _parse_foreign_key_constraint(
    definition: str,
    table_name: str,
) -> SchemaForeignKey | None:
    """Parse a simple table-level FOREIGN KEY constraint if present."""

    match = re.search(
        r"FOREIGN\s+KEY\s*\((?P<from>[^)]+)\)\s+"
        r"REFERENCES\s+(?P<table>\"(?:\"\"|[^\"])+\"|`[^`]+`|\[[^\]]+\]|[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?)"
        r"\s*\((?P<to>[^)]+)\)",
        definition,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None

    from_column = _normalize_sql_identifier(match.group("from").split(",", 1)[0].strip())
    to_table = _normalize_sql_identifier(match.group("table"))
    to_column = _normalize_sql_identifier(match.group("to").split(",", 1)[0].strip())

    on_update = _extract_referential_action(definition, "UPDATE")
    on_delete = _extract_referential_action(definition, "DELETE")

    if not from_column or not to_table or not to_column:
        return None

    return SchemaForeignKey(
        table=table_name,
        from_column=from_column,
        to_table=to_table,
        to_column=to_column,
        on_update=on_update,
        on_delete=on_delete,
    )


def _extract_referential_action(definition: str, action_kind: str) -> str:
    """Extract ON UPDATE/DELETE action text from a foreign key definition."""

    match = re.search(
        rf"\bON\s+{re.escape(action_kind)}\s+"
        r"(CASCADE|RESTRICT|SET\s+NULL|SET\s+DEFAULT|NO\s+ACTION)",
        definition,
        re.IGNORECASE,
    )
    if match is None:
        return ""
    return " ".join(match.group(1).upper().split())


def _read_sql_identifier(text: str) -> tuple[str, str]:
    """Read the leading SQL identifier from text and return name plus rest."""

    stripped = text.lstrip()
    if not stripped:
        return "", ""

    first = stripped[0]
    if first == '"':
        return _read_quoted_identifier(stripped, '"', '"')
    if first == "`":
        return _read_quoted_identifier(stripped, "`", "`")
    if first == "[":
        return _read_quoted_identifier(stripped, "[", "]")

    match = re.match(r"([A-Za-z_][\w$]*)(.*)$", stripped, re.DOTALL)
    if match is None:
        return "", stripped

    return match.group(1), match.group(2).strip()


def _read_quoted_identifier(text: str, opener: str, closer: str) -> tuple[str, str]:
    """Read a quoted SQL identifier and return normalized name plus rest."""

    index = 1
    value: list[str] = []

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if char == closer:
            if opener == '"' and next_char == '"':
                value.append('"')
                index += 2
                continue
            return "".join(value), text[index + 1 :].strip()

        value.append(char)
        index += 1

    return "", text


def _normalize_sql_identifier(identifier: str) -> str:
    """Normalize quoted SQL identifiers without changing dotted names."""

    stripped = identifier.strip()
    if not stripped:
        return ""

    if stripped.startswith('"') and stripped.endswith('"'):
        return stripped[1:-1].replace('""', '"')
    if stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1]
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped[1:-1]

    return stripped


def _leading_sql_keyword(definition: str) -> str:
    """Return the first SQL keyword in uppercase."""

    match = re.match(r"\s*([A-Za-z_][\w$]*)", definition)
    if match is None:
        return ""
    return match.group(1).upper()


def _extract_column_data_type(remainder: str) -> str:
    """Extract a best-effort column data type from a column definition tail."""

    tokens = remainder.strip().split()
    data_type_tokens: list[str] = []

    for token in tokens:
        normalized_token = token.upper().rstrip(",")
        if normalized_token in _COLUMN_STOP_KEYWORDS:
            break
        data_type_tokens.append(token)

    return " ".join(data_type_tokens).strip()


def _extract_default_value(remainder: str) -> str | None:
    """Extract a compact DEFAULT value from a column definition tail."""

    match = re.search(r"\bDEFAULT\b\s+(.+)$", remainder, re.IGNORECASE | re.DOTALL)
    if match is None:
        return None

    value = match.group(1).strip()
    stop_match = re.search(
        r"\s+\b(PRIMARY|NOT|NULL|UNIQUE|CHECK|REFERENCES|COLLATE|GENERATED|CONSTRAINT)\b",
        value,
        re.IGNORECASE,
    )
    if stop_match is not None:
        value = value[: stop_match.start()].strip()

    return value or None


__all__ = [
    "DatabaseSchemaReport",
    "SQLITE_MAGIC_HEADER",
    "SQLITE_SCHEMA_EXTENSIONS",
    "SQL_SCHEMA_DIRECTORIES",
    "SQL_SCHEMA_FILE_EXTENSIONS",
    "SchemaColumn",
    "SchemaForeignKey",
    "SchemaIndex",
    "SchemaTable",
    "discover_database_schema_files",
    "parse_create_table_statement",
    "extract_sql_schema_file",
    "extract_create_table_statements_from_sql",
    "extract_sqlite_schema_file",
    "has_sqlite_magic_header",
    "is_generated_export_file",
    "is_sql_schema_candidate_path",
    "is_sqlite_candidate_path",
]
