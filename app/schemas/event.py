from __future__ import annotations

from datetime import date, time
from typing import Optional, List

from pydantic import BaseModel, Field


# -------- Evento --------
class EventoCreate(BaseModel):
    nome_evento: str = Field(..., min_length=2, max_length=200)
    local: str = Field(..., min_length=2, max_length=200)
    dt_ini: date
    dt_fim: date
    hr_ini: time
    hr_fim: time


class EventoUpdate(BaseModel):
    nome_evento: Optional[str] = Field(None, min_length=2, max_length=200)
    local: Optional[str] = Field(None, min_length=2, max_length=200)
    dt_ini: Optional[date] = None
    dt_fim: Optional[date] = None
    hr_ini: Optional[time] = None
    hr_fim: Optional[time] = None


class EventoOut(BaseModel):
    id: int
    nome_evento: str
    local: str
    dt_ini: date
    dt_fim: date
    hr_ini: time
    hr_fim: time

    model_config = {"from_attributes": True}


# -------- Lote --------
class LoteCreate(BaseModel):
    id_evento: int
    preco: float = Field(..., ge=0)
    num_lote: int = Field(..., gt=0)
    total_vagas: int = Field(..., ge=0)


class LoteUpdate(BaseModel):
    preco: Optional[float] = Field(None, ge=0)
    num_lote: Optional[int] = Field(None, gt=0)
    total_vagas: Optional[int] = Field(None, ge=0)


class LoteOut(BaseModel):
    id: int
    id_evento: int
    preco: float
    num_lote: int
    total_vagas: int

    model_config = {"from_attributes": True}


# -------- Produto --------
class ProdutoCreate(BaseModel):
    id_evento: int
    preco: float = Field(..., ge=0)
    descricao: str = Field(..., min_length=1, max_length=255)
    img: Optional[str] = None  # S3 URL ou key


class ProdutoUpdate(BaseModel):
    preco: Optional[float] = Field(None, ge=0)
    descricao: Optional[str] = Field(None, min_length=1, max_length=255)
    img: Optional[str] = None


class ProdutoOut(BaseModel):
    id: int
    id_evento: int
    preco: float
    descricao: str
    img: Optional[str] = None

    model_config = {"from_attributes": True}

class EventoInfoOut(BaseModel):
    evento: EventoOut
    lotes: list[LoteOut]
    produtos: list[ProdutoOut]