"""Configuração SQLAlchemy, sessões e proteção do esquema SQLite Rev1."""

import os
import re
from collections.abc import Generator

from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, event, inspect
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./projects.db")
_engine_options = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **_engine_options)

# Independent of the application version; identifies the compatible Rev1 schema.
SCHEMA_VERSION = 1
_SCHEMA_TABLES = {"projects", "phase_history"}


class SchemaCompatibilityError(RuntimeError):
    """Startup cannot safely use the configured database."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"Inicialização interrompida: {reason} "
            "Confira DATABASE_URL e siga docs/banco-novo-rev1.md. "
            "Se o arquivo configurado for legado ou incompatível, preserve-o e "
            "escolha outro arquivo SQLite vazio para a Rev1, com autorização "
            "da operação. "
            "A inicialização não migra nem apaga dados de bancos existentes; "
            "create_all não migra tabelas existentes."
        )


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _normalize_check(expression: str) -> str:
    """Ignore SQL spacing/case outside string literals, preserving their values."""
    parts = re.split(r"('(?:''|[^'])*')", expression)
    return "".join(
        part if index % 2 else re.sub(r"\s+", "", part).upper()
        for index, part in enumerate(parts)
    )


def _type_name(sql_type, connection: Connection) -> str:
    # SQLite reflection omits collation; the business-key index is checked below.
    compiled = sql_type.compile(dialect=connection.dialect)
    return compiled.upper().split(" COLLATE ", 1)[0].replace(" ", "")


def _verify_business_key_collation(connection: Connection) -> None:
    """Require a complete, case-sensitive unique key, including leading zeros."""
    key = ("codigo_projeto", "codigo_subprojeto", "edicao")
    for index in connection.exec_driver_sql("PRAGMA index_list('projects')").mappings():
        if not index["unique"] or index["partial"]:
            continue
        quoted = connection.dialect.identifier_preparer.quote_identifier(index["name"])
        columns = [
            row for row in connection.exec_driver_sql(
                f"PRAGMA index_xinfo({quoted})"
            ).mappings() if row["key"]
        ]
        if tuple(row["name"] for row in columns) == key and all(
            row["coll"].upper() == "BINARY" and not row["desc"] for row in columns
        ):
            return
    raise SchemaCompatibilityError("a chave única D01 não possui a comparação esperada.")


def _verify_schema(connection: Connection) -> None:
    """Inspect metadata only; never query new ORM columns before compatibility."""
    inspector = inspect(connection)
    if set(inspector.get_table_names()) != _SCHEMA_TABLES:
        raise SchemaCompatibilityError("as tabelas estão ausentes, incompletas ou desconhecidas.")
    if inspector.get_view_names() or connection.exec_driver_sql(
        "SELECT 1 FROM sqlite_master WHERE type = 'trigger' LIMIT 1"
    ).first():
        raise SchemaCompatibilityError("há views ou triggers fora do esquema Rev1.")

    for table in Base.metadata.sorted_tables:
        columns = {column["name"]: column for column in inspector.get_columns(table.name)}
        if set(columns) != set(table.columns.keys()):
            raise SchemaCompatibilityError(f"a tabela {table.name} tem colunas incompatíveis.")
        for column in table.columns:
            actual = columns[column.name]
            if (
                _type_name(actual["type"], connection) != _type_name(column.type, connection)
                or actual["nullable"] != column.nullable
                or actual.get("default") is not None
                or actual.get("computed") is not None
            ):
                raise SchemaCompatibilityError(
                    f"a definição de {table.name}.{column.name} é incompatível."
                )

        primary_key = inspector.get_pk_constraint(table.name)["constrained_columns"]
        if tuple(primary_key) != tuple(column.name for column in table.primary_key):
            raise SchemaCompatibilityError(f"a chave primária de {table.name} é incompatível.")

        expected_unique = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
        }
        actual_unique = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(table.name)
        }
        if actual_unique != expected_unique:
            raise SchemaCompatibilityError(f"a unicidade de {table.name} é incompatível.")

        expected_checks = {
            _normalize_check(str(constraint.sqltext))
            for constraint in table.constraints if isinstance(constraint, CheckConstraint)
        }
        actual_checks = {
            _normalize_check(constraint["sqltext"])
            for constraint in inspector.get_check_constraints(table.name)
        }
        if actual_checks != expected_checks:
            raise SchemaCompatibilityError(f"as constraints de {table.name} são incompatíveis.")

        expected_foreign_keys = {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.referred_table.name,
                tuple(element.column.name for element in constraint.elements),
                (constraint.ondelete or "NO ACTION").upper(),
                (constraint.onupdate or "NO ACTION").upper(),
            )
            for constraint in table.foreign_key_constraints
        }
        actual_foreign_keys = {
            (
                tuple(constraint["constrained_columns"]),
                constraint["referred_table"],
                tuple(constraint["referred_columns"]),
                (constraint.get("options", {}).get("ondelete") or "NO ACTION").upper(),
                (constraint.get("options", {}).get("onupdate") or "NO ACTION").upper(),
            )
            for constraint in inspector.get_foreign_keys(table.name)
        }
        if actual_foreign_keys != expected_foreign_keys:
            raise SchemaCompatibilityError(f"os vínculos de {table.name} são incompatíveis.")

        expected_indexes = {
            (index.name, tuple(column.name for column in index.columns), bool(index.unique))
            for index in table.indexes
        }
        actual_indexes = inspector.get_indexes(table.name)
        if any(index.get("dialect_options", {}).get("sqlite_where") is not None
               for index in actual_indexes) or {
            (index["name"], tuple(index["column_names"]), bool(index["unique"]))
            for index in actual_indexes
        } != expected_indexes:
            raise SchemaCompatibilityError(f"os índices de {table.name} são incompatíveis.")

    _verify_business_key_collation(connection)


def initialize_database(database_engine: Engine) -> None:
    """Create only an empty SQLite schema; reject legacy/partial schemas unchanged.

    Models must already be registered. Explicit BEGIN keeps SQLite DDL and the
    version marker in one transaction, including with legacy sqlite3 transaction
    control. Existing databases receive no automatic schema or data changes.
    """
    if database_engine.dialect.name != "sqlite":
        raise SchemaCompatibilityError("esta revisão suporta inicialização apenas em SQLite.")
    if set(Base.metadata.tables) != _SCHEMA_TABLES:
        raise SchemaCompatibilityError("os models Rev1 não foram registrados corretamente.")

    try:
        with database_engine.connect() as connection:
            # Connection-local setting, before the explicit transaction.
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            if connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() != 1:
                raise SchemaCompatibilityError("não foi possível ativar as chaves estrangeiras.")
            connection.commit()
            try:
                connection.exec_driver_sql("BEGIN")
                objects = connection.exec_driver_sql(
                    "SELECT type, name FROM sqlite_master "
                    "WHERE name NOT GLOB 'sqlite_*'"
                ).all()
                version = connection.exec_driver_sql("PRAGMA user_version").scalar_one()
                if not objects and version == 0:
                    Base.metadata.create_all(bind=connection, checkfirst=False)
                    _verify_schema(connection)
                    connection.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")
                else:
                    if version != SCHEMA_VERSION:
                        reason = f"a versão do esquema é {version}; esperada {SCHEMA_VERSION}."
                        if version == 0:
                            reason = "o banco possui esquema legado ou sem versão concluída."
                        raise SchemaCompatibilityError(reason)
                    _verify_schema(connection)

                if connection.exec_driver_sql("PRAGMA foreign_key_check").first():
                    raise SchemaCompatibilityError("existem referências órfãs no banco.")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except SQLAlchemyError as error:
        raise SchemaCompatibilityError(
            "não foi possível ler ou inicializar o esquema SQLite com segurança."
        ) from error


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
