from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pytest

from repocontext.schema import (
    DatabaseSchemaReport,
    SchemaColumn,
    SchemaForeignKey,
    SchemaIndex,
    SchemaTable,
    discover_database_schema_files,
    extract_sqlite_schema_file,
    has_sqlite_magic_header,
    is_generated_export_file,
    is_sql_schema_candidate_path,
    is_sqlite_candidate_path,
)


@dataclass
class FileInfoLike:
    relative_path: Path
    absolute_path: Path


def create_sqlite_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.commit()
    finally:
        connection.close()


def test_schema_column_normalizes_values_and_exposes_primary_key() -> None:
    column = SchemaColumn(
        name=" id ",
        data_type=" INTEGER ",
        nullable=False,
        default_value=None,
        primary_key_position=1,
        position=0,
        raw_definition=" id INTEGER PRIMARY KEY ",
    )

    assert column.name == "id"
    assert column.data_type == "INTEGER"
    assert column.raw_definition == "id INTEGER PRIMARY KEY"
    assert column.position == 0
    assert column.is_primary_key is True


def test_schema_column_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        SchemaColumn(name="   ")


def test_schema_column_rejects_negative_position() -> None:
    with pytest.raises(ValueError):
        SchemaColumn(name="id", position=-1)


def test_schema_foreign_key_normalizes_values() -> None:
    foreign_key = SchemaForeignKey(
        table=" users ",
        from_column=" role_id ",
        to_table=" roles ",
        to_column=" id ",
        on_update=" CASCADE ",
        on_delete=" RESTRICT ",
    )

    assert foreign_key.table == "users"
    assert foreign_key.from_column == "role_id"
    assert foreign_key.to_table == "roles"
    assert foreign_key.to_column == "id"
    assert foreign_key.on_update == "CASCADE"
    assert foreign_key.on_delete == "RESTRICT"


def test_schema_index_normalizes_columns() -> None:
    index = SchemaIndex(
        name=" users_email_idx ",
        table=" users ",
        unique=True,
        columns=(" email ", "", " name "),
        origin=" c ",
    )

    assert index.name == "users_email_idx"
    assert index.table == "users"
    assert index.unique is True
    assert index.columns == ("email", "name")
    assert index.origin == "c"


def test_schema_table_sorts_nested_schema_items() -> None:
    table = SchemaTable(
        name="users",
        source_file=Path("data/app.sqlite").as_posix(),
        columns=(
            SchemaColumn(name="name", position=1),
            SchemaColumn(name="id", primary_key_position=1, position=0),
        ),
        foreign_keys=(
            SchemaForeignKey(table="users", from_column="team_id", to_table="teams", to_column="id"),
            SchemaForeignKey(table="users", from_column="role_id", to_table="roles", to_column="id"),
        ),
        indexes=(
            SchemaIndex(name="z_idx", table="users"),
            SchemaIndex(name="a_idx", table="users"),
        ),
    )

    assert [column.name for column in table.columns] == ["id", "name"]
    assert [foreign_key.from_column for foreign_key in table.foreign_keys] == ["role_id", "team_id"]
    assert [index.name for index in table.indexes] == ["a_idx", "z_idx"]


def test_database_schema_report_sorts_and_deduplicates_paths_and_tables() -> None:
    report = DatabaseSchemaReport(
        database_files=("z.sqlite", "a.sqlite", "a.sqlite"),
        sql_schema_files=("schema/z.sql", "schema/a.sql"),
        unsupported_files=("broken.db", "broken.db"),
        tables=(
            SchemaTable(name="z_table", source_file="z.sqlite"),
            SchemaTable(name="a_table", source_file="a.sqlite"),
        ),
    )

    assert report.database_files == ("a.sqlite", "z.sqlite")
    assert report.sql_schema_files == ("schema/a.sql", "schema/z.sql")
    assert report.unsupported_files == ("broken.db",)
    assert [table.name for table in report.tables] == ["a_table", "z_table"]


def test_database_schema_report_can_be_empty() -> None:
    report = DatabaseSchemaReport()

    assert report.is_empty() is True


def test_sqlite_candidate_path_detection() -> None:
    assert is_sqlite_candidate_path("data/app.sqlite") is True
    assert is_sqlite_candidate_path("data/app.sqlite3") is True
    assert is_sqlite_candidate_path("data/app.db") is True
    assert is_sqlite_candidate_path("data/app.db3") is True
    assert is_sqlite_candidate_path("data/app.s3db") is True
    assert is_sqlite_candidate_path("src/app.py") is False
    assert is_sqlite_candidate_path("full.txt") is False


def test_sql_schema_candidate_path_detection() -> None:
    assert is_sql_schema_candidate_path("schema.sql") is True
    assert is_sql_schema_candidate_path("migrations/001_init.txt") is True
    assert is_sql_schema_candidate_path("schema/tables.txt") is True
    assert is_sql_schema_candidate_path("sql/init.txt") is True
    assert is_sql_schema_candidate_path("src/app.py") is False
    assert is_sql_schema_candidate_path("ai.txt") is False


def test_generated_export_detection() -> None:
    assert is_generated_export_file("full.txt") is True
    assert is_generated_export_file("ai.txt") is True
    assert is_generated_export_file("docs.txt") is True
    assert is_generated_export_file("changed.txt") is True
    assert is_generated_export_file("README.md") is False


def test_sqlite_magic_header_detection(tmp_path: Path) -> None:
    database_path = tmp_path / "database.sqlite"
    create_sqlite_database(database_path)

    assert has_sqlite_magic_header(database_path) is True


def test_sqlite_magic_header_rejects_non_sqlite_file(tmp_path: Path) -> None:
    fake_database_path = tmp_path / "random.db"
    fake_database_path.write_bytes(b"not sqlite")

    assert has_sqlite_magic_header(fake_database_path) is False




def test_extract_sqlite_schema_file_preserves_sqlite_column_order(tmp_path: Path) -> None:
    database_path = tmp_path / "ordered.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    users_table = report.tables[0]
    assert [column.name for column in users_table.columns] == ["id", "role_id", "email"]
    assert [column.position for column in users_table.columns] == [0, 1, 2]

def test_extract_sqlite_schema_file_reads_simple_table(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite"
    create_sqlite_database(database_path)

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert report.database_files == ("app.sqlite",)
    assert report.warnings == ()
    assert report.unsupported_files == ()
    assert [table.name for table in report.tables] == ["users"]

    users_table = report.tables[0]
    assert users_table.source_file == "app.sqlite"
    assert users_table.table_type == "table"
    assert [column.name for column in users_table.columns] == ["id", "name"]
    assert users_table.columns[0].data_type == "INTEGER"
    assert users_table.columns[0].is_primary_key is True
    assert users_table.columns[1].data_type == "TEXT"
    assert users_table.columns[1].nullable is False


def test_extract_sqlite_schema_file_reads_multiple_tables_foreign_key_and_index(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "app.sqlite"
    database_path.parent.mkdir(parents=True)

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                email TEXT NOT NULL DEFAULT 'unknown',
                FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE UNIQUE INDEX users_email_idx ON users(email)")
        connection.commit()
    finally:
        connection.close()

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert [table.name for table in report.tables] == ["roles", "users"]

    users_table = next(table for table in report.tables if table.name == "users")
    assert [column.name for column in users_table.columns] == ["id", "role_id", "email"]

    email_column = next(column for column in users_table.columns if column.name == "email")
    assert email_column.data_type == "TEXT"
    assert email_column.nullable is False
    assert email_column.default_value == "'unknown'"

    assert len(users_table.foreign_keys) == 1
    foreign_key = users_table.foreign_keys[0]
    assert foreign_key.from_column == "role_id"
    assert foreign_key.to_table == "roles"
    assert foreign_key.to_column == "id"
    assert foreign_key.on_delete == "CASCADE"

    assert len(users_table.indexes) == 1
    index = users_table.indexes[0]
    assert index.name == "users_email_idx"
    assert index.unique is True
    assert index.columns == ("email",)


def test_extract_sqlite_schema_file_reads_views_separately(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("CREATE VIEW active_users AS SELECT id, name FROM users")
        connection.commit()
    finally:
        connection.close()

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert [table.name for table in report.tables] == ["users"]
    assert [view.name for view in report.views] == ["active_users"]
    assert report.views[0].table_type == "view"
    assert [column.name for column in report.views[0].columns] == ["id", "name"]


def test_extract_sqlite_schema_file_filters_internal_sqlite_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        connection.commit()
    finally:
        connection.close()

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert [table.name for table in report.tables] == ["users"]
    assert "sqlite_sequence" not in [table.name for table in report.tables]


def test_extract_sqlite_schema_file_marks_non_sqlite_file_as_unsupported(tmp_path: Path) -> None:
    database_path = tmp_path / "broken.sqlite"
    database_path.write_bytes(b"not sqlite")

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert report.database_files == ()
    assert report.unsupported_files == ("broken.sqlite",)
    assert "broken.sqlite: file extension suggests SQLite but magic header is missing" in report.warnings


def test_extract_sqlite_schema_file_handles_corrupt_sqlite_database_without_crashing(tmp_path: Path) -> None:
    database_path = tmp_path / "corrupt.sqlite"
    database_path.write_bytes(b"SQLite format 3\x00" + b"broken data")

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)

    assert report.database_files == ("corrupt.sqlite",)
    assert report.tables == ()
    assert report.views == ()
    assert any("could not read SQLite schema" in warning or "could not open SQLite database" in warning for warning in report.warnings)


def test_extract_sqlite_schema_file_does_not_export_table_data(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO users (name) VALUES ('VerySecretUserName')")
        connection.commit()
    finally:
        connection.close()

    report = extract_sqlite_schema_file(database_path, repo_root=tmp_path)
    report_text = repr(report)

    assert "users" in report_text
    assert "name" in report_text
    assert "VerySecretUserName" not in report_text


def test_discover_database_schema_files_does_not_scan_filesystem_without_explicit_files(tmp_path: Path) -> None:
    database_path = tmp_path / "untracked.sqlite"
    create_sqlite_database(database_path)

    report = discover_database_schema_files(tmp_path)

    assert report.is_empty() is True


def test_discover_database_schema_files_can_opt_into_filesystem_scan(tmp_path: Path) -> None:
    database_path = tmp_path / "diagnostic.sqlite"
    create_sqlite_database(database_path)

    report = discover_database_schema_files(tmp_path, allow_filesystem_scan=True)

    assert report.database_files == ("diagnostic.sqlite",)

def test_discover_database_schema_files_detects_sqlite_and_sql_files(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "app.sqlite"
    create_sqlite_database(database_path)

    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE logs (id INTEGER PRIMARY KEY);", encoding="utf-8")

    python_path = tmp_path / "src" / "app.py"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("print('hello')\n", encoding="utf-8")

    report = discover_database_schema_files(
        tmp_path,
        files=[
            Path("data/app.sqlite"),
            Path("schema.sql"),
            Path("src/app.py"),
        ],
    )

    assert report.database_files == ("data/app.sqlite",)
    assert report.sql_schema_files == ("schema.sql",)
    assert report.unsupported_files == ()
    assert report.warnings == ()


def test_discover_database_schema_files_marks_fake_db_as_unsupported(tmp_path: Path) -> None:
    fake_database_path = tmp_path / "random.db"
    fake_database_path.write_bytes(b"not sqlite")

    report = discover_database_schema_files(tmp_path, files=[Path("random.db")])

    assert report.database_files == ()
    assert report.unsupported_files == ("random.db",)
    assert "random.db: file extension suggests SQLite but magic header is missing" in report.warnings


def test_discover_database_schema_files_excludes_generated_exports(tmp_path: Path) -> None:
    for file_name in ("full.txt", "ai.txt", "docs.txt", "changed.txt"):
        (tmp_path / file_name).write_text("generated", encoding="utf-8")

    report = discover_database_schema_files(
        tmp_path,
        files=[Path("full.txt"), Path("ai.txt"), Path("docs.txt"), Path("changed.txt")],
    )

    assert report.is_empty() is True


def test_discover_database_schema_files_accepts_fileinfo_like_objects(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "app.sqlite"
    create_sqlite_database(database_path)

    file_info = FileInfoLike(
        relative_path=Path("data/app.sqlite"),
        absolute_path=database_path,
    )

    report = discover_database_schema_files(tmp_path, files=[file_info])

    assert report.database_files == ("data/app.sqlite",)


def test_discover_database_schema_files_uses_files_argument_as_scope(tmp_path: Path) -> None:
    tracked_database = tmp_path / "tracked.sqlite"
    untracked_database = tmp_path / "untracked.sqlite"
    create_sqlite_database(tracked_database)
    create_sqlite_database(untracked_database)

    report = discover_database_schema_files(tmp_path, files=[Path("tracked.sqlite")])

    assert report.database_files == ("tracked.sqlite",)
    assert "untracked.sqlite" not in report.database_files
