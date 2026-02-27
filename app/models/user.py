from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Pessoa(Base):
    __tablename__ = "tb_pessoa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    cpf: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True)
    adm: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        back_populates="pessoa",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Usuario(Base):
    __tablename__ = "tb_usuario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_pessoa: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_pessoa.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, unique=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pessoa: Mapped["Pessoa"] = relationship("Pessoa", back_populates="usuario")


class TokenBlacklist(Base):
    __tablename__ = "tb_blacklist"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    data_insercao: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)