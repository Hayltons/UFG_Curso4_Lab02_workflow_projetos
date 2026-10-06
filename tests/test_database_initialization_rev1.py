"""Schema initialization and rejection checks; all files belong to tmp_path."""

import sqlite3

import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import SCHEMA_VERSION, SchemaCompatibilityError, initialize_database
from app.models.project import PhaseHistoryEntity, ProjectCreate, ProjectEntity
from app.services.project_service import ProjectService


def test_empty_database_creates_versioned_schema_and_is_idempotent(tmp_path):
    path = tmp_path / "empty.db"
    engine = create_engine(f"sqlite:///{path}")
    try:
        initialize_database(engine)
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA user_version").scalar_one() == SCHEMA_VERSION
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
            assert connection.exec_driver_sql("SELECT count(*) FROM projects").scalar_one() == 0
            assert connection.exec_driver_sql("SELECT count(*) FROM phase_history").scalar_one() == 0
            assert set(inspect(connection).get_table_names()) == {"projects", "phase_history"}
            assert inspect(connection).get_check_constraints("projects")
        before = path.read_bytes()
        initialize_database(engine)
        assert path.read_bytes() == before
    finally:
        engine.dispose()


@pytest.mark.parametrize("ddl", [
    "CREATE TABLE projects (id INTEGER PRIMARY KEY, titulo TEXT); "
    "INSERT INTO projects VALUES (1, 'Dado legado');",
    "CREATE TABLE unknown_data (id INTEGER); INSERT INTO unknown_data VALUES (7);",
    "CREATE TABLE projects (id INTEGER PRIMARY KEY); PRAGMA user_version=-1;",
    "CREATE TABLE projects (id INTEGER PRIMARY KEY); PRAGMA user_version=1;",
    "PRAGMA user_version=1;",
    "PRAGMA user_version=99;",
])
def test_legacy_unknown_partial_or_stamped_schemas_are_preserved(tmp_path, ddl):
    path = tmp_path / "incompatible.db"
    with sqlite3.connect(path) as db:
        db.executescript(ddl)
    before = path.read_bytes()
    engine = create_engine(f"sqlite:///{path}")
    try:
        with pytest.raises(SchemaCompatibilityError) as error:
            initialize_database(engine)
        assert "docs/banco-novo-rev1.md" in str(error.value)
        assert "outro arquivo SQLite vazio" in str(error.value)
        assert path.read_bytes() == before
    finally:
        engine.dispose()


@pytest.mark.parametrize("mutation", [
    "PRAGMA user_version=2",
    "ALTER TABLE projects ADD COLUMN unexpected TEXT",
    "ALTER TABLE projects RENAME COLUMN codigo_subprojeto TO old_code",
    "DROP INDEX ix_projects_id",
    "CREATE INDEX extra_index ON projects(titulo)",
    "CREATE TABLE unknown_data (id INTEGER)",
    "CREATE VIEW unexpected_view AS SELECT id FROM projects",
    "CREATE TRIGGER unexpected_trigger AFTER INSERT ON projects BEGIN SELECT 1; END",
])
def test_schema_structure_is_checked_even_when_version_exists(tmp_path, mutation):
    path = tmp_path / "changed.db"
    engine = create_engine(f"sqlite:///{path}")
    initialize_database(engine)
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute(mutation)
    before = path.read_bytes()
    try:
        with pytest.raises(SchemaCompatibilityError):
            initialize_database(engine)
        assert path.read_bytes() == before
    finally:
        engine.dispose()


@pytest.mark.parametrize("failure_point", ["second_table", "version_marker"])
def test_failed_creation_rolls_back_tables_and_version(tmp_path, failure_point):
    path = tmp_path / "interrupted.db"
    engine = create_engine(f"sqlite:///{path}")
    table_count = 0

    def inject_failure(connection, cursor, statement, parameters, context, executemany):
        nonlocal table_count
        if statement.lstrip().startswith("CREATE TABLE"):
            table_count += 1
        fail = (
            failure_point == "second_table"
            and statement.lstrip().startswith("CREATE TABLE") and table_count == 2
        ) or (
            failure_point == "version_marker"
            and statement.startswith("PRAGMA user_version =")
        )
        if fail:
            raise OperationalError(statement, parameters, RuntimeError("injected DDL failure"))

    event.listen(engine, "before_cursor_execute", inject_failure)
    try:
        with pytest.raises(SchemaCompatibilityError):
            initialize_database(engine)
    finally:
        event.remove(engine, "before_cursor_execute", inject_failure)
    try:
        with sqlite3.connect(path) as db:
            assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
            assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        initialize_database(engine)
        assert set(inspect(engine).get_table_names()) == {"projects", "phase_history"}
    finally:
        engine.dispose()


def test_orphan_history_blocks_startup_without_deleting_data(tmp_path):
    path = tmp_path / "orphan.db"
    engine = create_engine(f"sqlite:///{path}")
    initialize_database(engine)
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute(
            "INSERT INTO phase_history "
            "(projeto_id, fase_destino, data_inicio_fase, alterado_em) "
            "VALUES (999, 'selecao', '2026-10-05', '2026-10-05 12:00:00')"
        )
    before = path.read_bytes()
    try:
        with pytest.raises(SchemaCompatibilityError, match="órfãs"):
            initialize_database(engine)
        assert path.read_bytes() == before
    finally:
        engine.dispose()


def test_database_enforces_foreign_keys_and_delete_cascade(tmp_path):
    path = tmp_path / "foreign-keys.db"
    engine = create_engine(f"sqlite:///{path}")
    initialize_database(engine)
    try:
        with Session(engine, expire_on_commit=False) as session:
            project = ProjectService(session).create_project(ProjectCreate(
                codigo_projeto="01.002", codigo_subprojeto="03", titulo="Projeto",
                nome_subprojeto="Subprojeto", edicao="2026", selecionados=10,
                avisados=8, descartados=8,
            ))
            project_id = project.id
        with engine.begin() as connection:
            connection.exec_driver_sql("DELETE FROM projects WHERE id = ?", (project_id,))
            assert connection.exec_driver_sql("SELECT count(*) FROM phase_history").scalar_one() == 0
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        initialize_database(engine)
        with Session(engine) as session:
            assert session.scalars(select(ProjectEntity)).all() == []
            assert session.scalars(select(PhaseHistoryEntity)).all() == []
    finally:
        engine.dispose()
