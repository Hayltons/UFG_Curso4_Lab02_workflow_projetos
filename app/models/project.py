"""Project workflow contracts, enums, and SQLAlchemy entities for Rev1."""

from datetime import UTC, date, datetime
from enum import StrEnum
import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.database import Base


class ProjectPhase(StrEnum):
    SELECAO = "selecao"
    DESENVOLVIMENTO = "desenvolvimento"
    EXECUCAO = "execucao"
    POS_VENDA = "pos_venda"
    ENCERRADO = "encerrado"


PHASE_ORDER = tuple(ProjectPhase)
_PHASE_VALUES = ", ".join(f"'{phase.value}'" for phase in PHASE_ORDER)


def allowed_next_phases(phase: ProjectPhase) -> list[ProjectPhase]:
    """Return the single allowed next phase, or none for the terminal phase."""
    index = PHASE_ORDER.index(phase)
    if index + 1 >= len(PHASE_ORDER):
        return []
    return [PHASE_ORDER[index + 1]]


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """SQLite drops timezone metadata; expose database timestamps as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Store UTC timestamps consistently and restore their timezone on SQLite."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        normalized = as_utc(value)
        if dialect.name == "sqlite":
            return normalized.replace(tzinfo=None)
        return normalized

    def process_result_value(self, value: datetime | None, _dialect):
        return as_utc(value) if value is not None else None


# These checks target the SQLite database used by this MVP. String(n) alone does
# not enforce a length limit there; the Pydantic contracts enforce it at the API.
_PROJECT_CHECKS = (
    CheckConstraint(
        "length(codigo_projeto) = 6 AND "
        "codigo_projeto GLOB '[0-9][0-9].[0-9][0-9][0-9]'",
        name="ck_projects_codigo_projeto",
    ),
    CheckConstraint(
        "length(codigo_subprojeto) = 2 AND "
        "codigo_subprojeto GLOB '[0-9][0-9]'",
        name="ck_projects_codigo_subprojeto",
    ),
    CheckConstraint(
        "length(titulo) BETWEEN 1 AND 150 AND length(trim(titulo)) > 0",
        name="ck_projects_titulo",
    ),
    CheckConstraint(
        "length(nome_subprojeto) BETWEEN 1 AND 150 AND "
        "length(trim(nome_subprojeto)) > 0",
        name="ck_projects_nome_subprojeto",
    ),
    CheckConstraint(
        "length(edicao) BETWEEN 1 AND 30 AND length(trim(edicao)) > 0",
        name="ck_projects_edicao",
    ),
    CheckConstraint(
        "equipe IS NULL OR length(equipe) <= 50",
        name="ck_projects_equipe",
    ),
    CheckConstraint(f"fase IN ({_PHASE_VALUES})", name="ck_projects_fase"),
    CheckConstraint(
        "selecionados > 0 AND avisados > 0 AND descartados > 0 "
        "AND avisados <= selecionados AND descartados <= avisados",
        name="ck_projects_contagens",
    ),
    CheckConstraint(
        "estoque = selecionados - avisados AND "
        "executados = avisados - descartados",
        name="ck_projects_derivados",
    ),
)


class ProjectEntity(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint(
            "codigo_projeto", "codigo_subprojeto", "edicao",
            name="uq_projects_codigo_subprojeto_edicao",
        ),
        *_PROJECT_CHECKS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_projeto: Mapped[str] = mapped_column(String(6), nullable=False)
    codigo_subprojeto: Mapped[str] = mapped_column(String(2), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_subprojeto: Mapped[str] = mapped_column(String(150), nullable=False)
    edicao: Mapped[str] = mapped_column(String(30, collation="BINARY"), nullable=False)
    equipe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_prevista_execucao: Mapped[date | None] = mapped_column(Date, nullable=True)
    fase: Mapped[str] = mapped_column(String(30), nullable=False, default=ProjectPhase.SELECAO.value)
    data_inicio_fase: Mapped[date] = mapped_column(Date, nullable=False)
    data_entrada_fase: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    selecionados: Mapped[int] = mapped_column(Integer, nullable=False)
    avisados: Mapped[int] = mapped_column(Integer, nullable=False)
    descartados: Mapped[int] = mapped_column(Integer, nullable=False)
    estoque: Mapped[int] = mapped_column(Integer, nullable=False)
    executados: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    historico: Mapped[list["PhaseHistoryEntity"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan", passive_deletes=True,
        order_by="PhaseHistoryEntity.id",
    )


class PhaseHistoryEntity(Base):
    __tablename__ = "phase_history"
    __table_args__ = (
        CheckConstraint(
            f"fase_origem IS NULL OR fase_origem IN ({_PHASE_VALUES})",
            name="ck_phase_history_fase_origem",
        ),
        CheckConstraint(
            f"fase_destino IN ({_PHASE_VALUES})",
            name="ck_phase_history_fase_destino",
        ),
        CheckConstraint(
            "codigo_projeto IS NULL OR (length(codigo_projeto) = 6 AND "
            "codigo_projeto GLOB '[0-9][0-9].[0-9][0-9][0-9]')",
            name="ck_phase_history_codigo_projeto",
        ),
        CheckConstraint(
            "codigo_subprojeto IS NULL OR (length(codigo_subprojeto) = 2 AND "
            "codigo_subprojeto GLOB '[0-9][0-9]')",
            name="ck_phase_history_codigo_subprojeto",
        ),
        CheckConstraint(
            "titulo IS NULL OR (length(titulo) BETWEEN 1 AND 150 AND "
            "length(trim(titulo)) > 0)",
            name="ck_phase_history_titulo",
        ),
        CheckConstraint(
            "nome_subprojeto IS NULL OR (length(nome_subprojeto) BETWEEN 1 AND 150 "
            "AND length(trim(nome_subprojeto)) > 0)",
            name="ck_phase_history_nome_subprojeto",
        ),
        CheckConstraint(
            "edicao IS NULL OR (length(edicao) BETWEEN 1 AND 30 AND "
            "length(trim(edicao)) > 0)",
            name="ck_phase_history_edicao",
        ),
        CheckConstraint(
            "equipe IS NULL OR length(equipe) <= 50",
            name="ck_phase_history_equipe",
        ),
        CheckConstraint(
            "(selecionados IS NULL AND avisados IS NULL AND descartados IS NULL "
            "AND estoque IS NULL AND executados IS NULL) OR "
            "(selecionados IS NOT NULL AND avisados IS NOT NULL AND "
            "descartados IS NOT NULL AND estoque IS NOT NULL AND "
            "executados IS NOT NULL AND selecionados > 0 AND avisados > 0 "
            "AND descartados > 0 AND avisados <= selecionados "
            "AND descartados <= avisados AND estoque = selecionados - avisados "
            "AND executados = avisados - descartados)",
            name="ck_phase_history_contagens",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fase_origem: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fase_destino: Mapped[str] = mapped_column(String(30), nullable=False)
    data_inicio_fase: Mapped[date] = mapped_column(Date, nullable=False)
    alterado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    # Legacy events have no business-field snapshots. NULL means "not known",
    # not an invented historical value; new events will receive a full snapshot.
    codigo_projeto: Mapped[str | None] = mapped_column(String(6), nullable=True)
    codigo_subprojeto: Mapped[str | None] = mapped_column(String(2), nullable=True)
    titulo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nome_subprojeto: Mapped[str | None] = mapped_column(String(150), nullable=True)
    edicao: Mapped[str | None] = mapped_column(String(30), nullable=True)
    equipe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_prevista_execucao: Mapped[date | None] = mapped_column(Date, nullable=True)
    selecionados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avisados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descartados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estoque: Mapped[int | None] = mapped_column(Integer, nullable=True)
    executados: Mapped[int | None] = mapped_column(Integer, nullable=True)

    projeto: Mapped[ProjectEntity] = relationship(back_populates="historico")


def _strip_text(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _parse_iso_date(value: object) -> date:
    """Accept only a date object or JSON YYYY-MM-DD, never a timestamp/number."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Informe uma data válida em YYYY-MM-DD.") from exc
    raise ValueError("Informe uma data válida em YYYY-MM-DD.")


ProjectCode = Annotated[
    str, BeforeValidator(_strip_text),
    Field(strict=True, min_length=6, max_length=6, pattern=r"^[0-9]{2}\.[0-9]{3}$"),
]
SubprojectCode = Annotated[
    str, BeforeValidator(_strip_text),
    Field(strict=True, min_length=2, max_length=2, pattern=r"^[0-9]{2}$"),
]
NameText = Annotated[
    str, BeforeValidator(_strip_text), Field(strict=True, min_length=1, max_length=150),
]
EditionText = Annotated[
    str, BeforeValidator(_strip_text), Field(strict=True, min_length=1, max_length=30),
]
TeamText = Annotated[
    str, BeforeValidator(_strip_text), Field(strict=True, max_length=50),
]
PositiveCount = Annotated[int, Field(strict=True, gt=0)]
IsoDate = Annotated[date, BeforeValidator(_parse_iso_date)]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_projeto: ProjectCode
    codigo_subprojeto: SubprojectCode
    titulo: NameText
    nome_subprojeto: NameText
    edicao: EditionText
    equipe: TeamText | None = None
    data_prevista_execucao: IsoDate | None = None
    data_inicio_fase: IsoDate | None = None
    selecionados: PositiveCount
    avisados: PositiveCount
    descartados: PositiveCount

    @model_validator(mode="after")
    def valid_counts_and_date(self) -> "ProjectCreate":
        if self.avisados > self.selecionados:
            raise ValueError("Avisados deve ser menor ou igual a Selecionados.")
        if self.descartados > self.avisados:
            raise ValueError("Descartados deve ser menor ou igual a Avisados.")
        if "data_inicio_fase" in self.model_fields_set and self.data_inicio_fase is None:
            raise ValueError("Data de início da fase não pode ser nula.")
        return self


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_projeto: ProjectCode | None = None
    codigo_subprojeto: SubprojectCode | None = None
    titulo: NameText | None = None
    nome_subprojeto: NameText | None = None
    edicao: EditionText | None = None
    equipe: TeamText | None = None
    data_prevista_execucao: IsoDate | None = None
    data_inicio_fase: IsoDate | None = None
    selecionados: PositiveCount | None = None
    avisados: PositiveCount | None = None
    descartados: PositiveCount | None = None

    @model_validator(mode="after")
    def has_changes(self) -> "ProjectUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar.")
        required = {
            "codigo_projeto", "codigo_subprojeto", "titulo", "nome_subprojeto",
            "edicao", "data_inicio_fase", "selecionados", "avisados", "descartados",
        }
        if any(getattr(self, name) is None for name in required & self.model_fields_set):
            raise ValueError("Campos obrigatórios e contagens não podem ser nulos.")
        # Relations involving values omitted from PATCH are checked by the Service.
        return self


class PhaseHistoryUpdate(ProjectUpdate):
    """Patch business fields of a completed phase; identity/audit are forbidden."""


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_projeto: str
    codigo_subprojeto: str
    titulo: str
    nome_subprojeto: str
    edicao: str
    equipe: str | None
    data_prevista_execucao: date | None
    fase: ProjectPhase
    data_inicio_fase: date
    data_entrada_fase: datetime
    selecionados: int
    avisados: int
    descartados: int
    estoque: int
    executados: int
    criado_em: datetime
    atualizado_em: datetime
    transicoes_permitidas: list[ProjectPhase] = Field(default_factory=list)

    @field_validator("data_entrada_fase", "criado_em", "atualizado_em")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)


class PhaseChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fase: ProjectPhase
    data_inicio_fase: IsoDate | None = None

    @model_validator(mode="after")
    def explicit_date_cannot_be_null(self) -> "PhaseChange":
        if "data_inicio_fase" in self.model_fields_set and self.data_inicio_fase is None:
            raise ValueError("Data de início da fase não pode ser nula.")
        return self


class PhaseHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    projeto_id: int
    fase_origem: ProjectPhase | None
    fase_destino: ProjectPhase
    data_inicio_fase: date
    alterado_em: datetime
    codigo_projeto: str | None
    codigo_subprojeto: str | None
    titulo: str | None
    nome_subprojeto: str | None
    edicao: str | None
    equipe: str | None
    data_prevista_execucao: date | None
    selecionados: int | None
    avisados: int | None
    descartados: int | None
    estoque: int | None
    executados: int | None

    @field_validator("alterado_em")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)
