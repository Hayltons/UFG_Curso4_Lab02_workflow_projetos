"""Project workflow contracts, enums, and SQLAlchemy entities."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
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


class ProjectEntity(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    equipe: Mapped[str] = mapped_column(String(200), nullable=False)
    fase: Mapped[str] = mapped_column(String(30), nullable=False, default=ProjectPhase.SELECAO.value)
    data_entrada_fase: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    alvos_planejados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clientes_sensibilizados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indice_satisfacao: Mapped[float | None] = mapped_column(nullable=True)
    taxa_conversao: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    historico: Mapped[list["PhaseHistoryEntity"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan", passive_deletes=True,
        order_by="PhaseHistoryEntity.id",
    )


class PhaseHistoryEntity(Base):
    __tablename__ = "phase_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fase_origem: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fase_destino: Mapped[str] = mapped_column(String(30), nullable=False)
    alterado_em: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    projeto: Mapped[ProjectEntity] = relationship(back_populates="historico")


NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
SatisfactionScore = Annotated[float, Field(ge=0, le=10)]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Annotated[str, Field(min_length=1, max_length=200)]
    descricao: Annotated[str, Field(max_length=5000)] = ""
    equipe: Annotated[str, Field(min_length=1, max_length=200)]
    alvos_planejados: NonNegativeInt = 0
    clientes_sensibilizados: NonNegativeInt = 0
    indice_satisfacao: SatisfactionScore | None = None

    @field_validator("titulo", "equipe")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Este campo não pode ficar vazio.")
        return stripped


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    descricao: Annotated[str, Field(max_length=5000)] | None = None
    equipe: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    alvos_planejados: NonNegativeInt | None = None
    clientes_sensibilizados: NonNegativeInt | None = None
    indice_satisfacao: SatisfactionScore | None = None

    @field_validator("titulo", "equipe")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Este campo não pode ficar vazio.")
        return stripped

    @model_validator(mode="after")
    def has_changes(self) -> "ProjectUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar.")
        required_values = {"titulo", "descricao", "equipe", "alvos_planejados", "clientes_sensibilizados"}
        explicitly_null = required_values.intersection(self.model_fields_set)
        if any(getattr(self, name) is None for name in explicitly_null):
            raise ValueError("Campos cadastrais e contagens não podem ser nulos.")
        return self


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str
    equipe: str
    fase: ProjectPhase
    data_entrada_fase: datetime
    alvos_planejados: int
    clientes_sensibilizados: int
    indice_satisfacao: float | None
    taxa_conversao: Decimal | None
    criado_em: datetime
    atualizado_em: datetime
    transicoes_permitidas: list[ProjectPhase] = Field(default_factory=list)

    @field_validator("data_entrada_fase", "criado_em", "atualizado_em")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)

    @field_serializer("taxa_conversao")
    def serialize_conversion(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class PhaseChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fase: ProjectPhase


class PhaseHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    projeto_id: int
    fase_origem: ProjectPhase | None
    fase_destino: ProjectPhase
    alterado_em: datetime

    @field_validator("alterado_em")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)
