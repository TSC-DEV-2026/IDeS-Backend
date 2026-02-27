from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.event import Evento, Lote, Produto
from app.schemas.event import (
    EventoCreate, EventoUpdate, EventoOut,
    LoteCreate, LoteUpdate, LoteOut,
    ProdutoCreate, ProdutoUpdate, ProdutoOut, EventoInfoOut,
)

router = APIRouter()


# =========================
# EVENTOS
# =========================
@router.post("/eventos", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def criar_evento(payload: EventoCreate, db: Session = Depends(get_db)):
    if payload.dt_fim < payload.dt_ini:
        raise HTTPException(status_code=400, detail="dt_fim não pode ser menor que dt_ini")

    obj = Evento(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/eventos", response_model=list[EventoOut])
def listar_eventos(db: Session = Depends(get_db)):
    return db.execute(select(Evento).order_by(Evento.dt_ini.desc(), Evento.id.desc())).scalars().all()


@router.get("/eventos/{evento_id}", response_model=EventoOut)
def obter_evento(evento_id: int, db: Session = Depends(get_db)):
    obj = db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return obj


@router.put("/eventos/{evento_id}", response_model=EventoOut)
def atualizar_evento(evento_id: int, payload: EventoUpdate, db: Session = Depends(get_db)):
    obj = db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    data = payload.model_dump(exclude_unset=True)

    dt_ini = data.get("dt_ini", obj.dt_ini)
    dt_fim = data.get("dt_fim", obj.dt_fim)
    if dt_fim < dt_ini:
        raise HTTPException(status_code=400, detail="dt_fim não pode ser menor que dt_ini")

    for k, v in data.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_evento(evento_id: int, db: Session = Depends(get_db)):
    obj = db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    db.delete(obj)
    db.commit()
    return None


# =========================
# LOTES
# =========================
@router.post("/lotes", response_model=LoteOut, status_code=status.HTTP_201_CREATED)
def criar_lote(payload: LoteCreate, db: Session = Depends(get_db)):
    evento = db.execute(select(Evento.id).where(Evento.id == payload.id_evento)).scalar_one_or_none()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # garante (id_evento, num_lote) único
    existe = db.execute(
        select(Lote.id).where(Lote.id_evento == payload.id_evento, Lote.num_lote == payload.num_lote)
    ).scalar_one_or_none()
    if existe:
        raise HTTPException(status_code=409, detail="num_lote já existe para este evento")

    obj = Lote(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/lotes", response_model=list[LoteOut])
def listar_lotes(
    id_evento: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Lote).order_by(Lote.id.desc())
    if id_evento is not None:
        stmt = stmt.where(Lote.id_evento == id_evento)
    return db.execute(stmt).scalars().all()


@router.put("/lotes/{lote_id}", response_model=LoteOut)
def atualizar_lote(lote_id: int, payload: LoteUpdate, db: Session = Depends(get_db)):
    obj = db.execute(select(Lote).where(Lote.id == lote_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    data = payload.model_dump(exclude_unset=True)

    # se mudar num_lote, checa unicidade por evento
    if "num_lote" in data and data["num_lote"] != obj.num_lote:
        existe = db.execute(
            select(Lote.id).where(Lote.id_evento == obj.id_evento, Lote.num_lote == data["num_lote"])
        ).scalar_one_or_none()
        if existe:
            raise HTTPException(status_code=409, detail="num_lote já existe para este evento")

    for k, v in data.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/lotes/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_lote(lote_id: int, db: Session = Depends(get_db)):
    obj = db.execute(select(Lote).where(Lote.id == lote_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    db.delete(obj)
    db.commit()
    return None


# =========================
# PRODUTOS
# =========================
@router.post("/produtos", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(payload: ProdutoCreate, db: Session = Depends(get_db)):
    evento = db.execute(select(Evento.id).where(Evento.id == payload.id_evento)).scalar_one_or_none()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    obj = Produto(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(
    id_evento: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Produto).order_by(Produto.id.desc())
    if id_evento is not None:
        stmt = stmt.where(Produto.id_evento == id_evento)
    return db.execute(stmt).scalars().all()


@router.put("/produtos/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)):
    obj = db.execute(select(Produto).where(Produto.id == produto_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    obj = db.execute(select(Produto).where(Produto.id == produto_id)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    db.delete(obj)
    db.commit()
    return None

@router.get("/eventos/{evento_id}/info", response_model=EventoInfoOut)
def evento_info(evento_id: int, db: Session = Depends(get_db)):
    evento = db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    lotes = db.execute(
        select(Lote)
        .where(Lote.id_evento == evento_id)
        .order_by(Lote.num_lote.asc())
    ).scalars().all()

    produtos = db.execute(
        select(Produto)
        .where(Produto.id_evento == evento_id)
        .order_by(Produto.id.asc())
    ).scalars().all()

    return {
        "evento": evento,
        "lotes": lotes,
        "produtos": produtos,
    }