from __future__ import annotations

from datetime import date, time, datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Evento(Base):
    __tablename__ = "tb_eventos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    nome_evento: Mapped[str] = mapped_column(String(200), nullable=False)
    local: Mapped[str] = mapped_column(String(200), nullable=False)

    dt_ini: Mapped[date] = mapped_column(Date, nullable=False)
    dt_fim: Mapped[date] = mapped_column(Date, nullable=False)
    hr_ini: Mapped[time] = mapped_column(Time, nullable=False)
    hr_fim: Mapped[time] = mapped_column(Time, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lotes: Mapped[List["Lote"]] = relationship(
        "Lote",
        back_populates="evento",
        cascade="all, delete-orphan",
    )

    produtos: Mapped[List["Produto"]] = relationship(
        "Produto",
        back_populates="evento",
        cascade="all, delete-orphan",
    )


class Lote(Base):
    __tablename__ = "tb_lote"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    id_evento: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tb_eventos.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    num_lote: Mapped[int] = mapped_column(Integer, nullable=False)
    total_vagas: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    evento: Mapped["Evento"] = relationship("Evento", back_populates="lotes")


class Produto(Base):
    __tablename__ = "tb_produtos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    id_evento: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tb_eventos.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    img: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # S3 URL ou key

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    evento: Mapped["Evento"] = relationship("Evento", back_populates="produtos")