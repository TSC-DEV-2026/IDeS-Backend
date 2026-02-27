import os
import re
import uuid

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.user import Pessoa, Usuario, TokenBlacklist
from app.schemas.user import RegisterIn, RegisterOut
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import criar_token, verificar_token, decode_token

router = APIRouter()

load_dotenv()
is_prod = os.getenv("ENVIRONMENT") == "prod"
cookie_domain = "ziondocs.com.br" if is_prod else None

cookie_env = {
    "secure": True if is_prod else False,
    "samesite": "Lax",
    "domain": cookie_domain,
}

ACCESS_MAX_AGE = 60 * 60 * 24 * 7
REFRESH_MAX_AGE = 60 * 60 * 24 * 30


def _is_email(valor: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", (valor or "").strip()) is not None


def _cpf_digits(valor: str) -> str:
    return "".join(ch for ch in (valor or "") if ch.isdigit())


def _set_cookie_auth(resp: JSONResponse, access_token: str, refresh_token: str | None = None) -> None:
    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        max_age=ACCESS_MAX_AGE,
        path="/",
        **cookie_env,
    )
    if refresh_token:
        resp.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            max_age=REFRESH_MAX_AGE,
            path="/",
            **cookie_env,
        )
    resp.set_cookie(
        "logged_user",
        "true",
        httponly=False,
        max_age=ACCESS_MAX_AGE,
        path="/",
        **cookie_env,
    )


def _delete_cookie_auth(resp: Response) -> None:
    delete_kwargs = {"path": "/"}
    if cookie_domain:
        delete_kwargs["domain"] = cookie_domain

    resp.delete_cookie("access_token", **delete_kwargs)
    resp.delete_cookie("refresh_token", **delete_kwargs)
    resp.delete_cookie("logged_user", **delete_kwargs)


def _is_blacklisted(db: Session, jti: str | None) -> bool:
    if not jti:
        return True
    return db.scalar(select(TokenBlacklist.id).where(TokenBlacklist.jti == jti)) is not None


@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.usuario.email.strip().lower()

    if db.scalar(select(Usuario.id).where(Usuario.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")

    cpf = _cpf_digits(payload.pessoa.cpf or "")
    if cpf and db.scalar(select(Pessoa.id).where(Pessoa.cpf == cpf)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado")

    pessoa = Pessoa(
        nome=payload.pessoa.nome.strip(),
        cpf=cpf or None,
        data_nascimento=payload.pessoa.data_nascimento,
        adm=getattr(payload.pessoa, "adm", False) or False,
    )
    db.add(pessoa)
    db.flush()

    usuario = Usuario(
        pessoa_id=pessoa.id,
        email=email,
        senha_hash=hash_password(payload.usuario.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(pessoa)
    db.refresh(usuario)

    return RegisterOut(pessoa=pessoa, usuario=usuario)


class LoginInput(BaseModel):
    usuario: str
    senha: str


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(payload: LoginInput, db: Session = Depends(get_db)):
    ident = payload.usuario.strip()
    user: Usuario | None = None

    if _is_email(ident):
        email = ident.lower()
        user = db.execute(
            select(Usuario).options(joinedload(Usuario.pessoa)).where(Usuario.email == email)
        ).scalar_one_or_none()
    else:
        cpf = _cpf_digits(ident)
        pessoa = db.execute(select(Pessoa).where(Pessoa.cpf == cpf)).scalar_one_or_none()
        if pessoa:
            user = db.execute(
                select(Usuario).options(joinedload(Usuario.pessoa)).where(Usuario.pessoa_id == pessoa.id)
            ).scalar_one_or_none()

    if not user or not verify_password(payload.senha, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    access_payload = {"id": user.id, "sub": user.email, "tipo": "access", "jti": str(uuid.uuid4())}
    refresh_payload = {"id": user.id, "sub": user.email, "tipo": "refresh", "jti": str(uuid.uuid4())}

    access_token = criar_token(access_payload, expires_in=60 * 24 * 7)
    refresh_token = criar_token(refresh_payload, expires_in=60 * 24 * 30)

    resp = JSONResponse(content={"message": "Login com sucesso"})
    _set_cookie_auth(resp, access_token=access_token, refresh_token=refresh_token)
    return resp


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de autenticação ausente")

    payload = verificar_token(token)
    if not payload or payload.get("tipo") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    if _is_blacklisted(db, payload.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado ou inválido")

    uid = payload.get("id")
    try:
        uid = int(uid)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = db.execute(
        select(Usuario).options(joinedload(Usuario.pessoa)).where(Usuario.id == uid)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    return {
        "usuario": {"id": user.id, "email": user.email},
        "pessoa": {
            "id": user.pessoa.id if user.pessoa else None,
            "nome": user.pessoa.nome if user.pessoa else None,
            "cpf": user.pessoa.cpf if user.pessoa else None,
            "data_nascimento": user.pessoa.data_nascimento if user.pessoa else None,
            "adm": getattr(user.pessoa, "adm", False) if user.pessoa else False,
        },
    }


@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refreshToken não fornecido")

    payload = verificar_token(token)
    if not payload or payload.get("tipo") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refreshToken inválido ou expirado")

    if _is_blacklisted(db, payload.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refreshToken inválido ou expirado")

    uid = payload.get("id")
    try:
        uid = int(uid)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = db.execute(select(Usuario).where(Usuario.id == uid)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    novo_access = criar_token(
        {"id": user.id, "sub": user.email, "tipo": "access", "jti": str(uuid.uuid4())},
        expires_in=60 * 24 * 7,
    )

    resp = JSONResponse(content={"message": "Token renovado"})
    _set_cookie_auth(resp, access_token=novo_access, refresh_token=None)
    return resp


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    def _revoke(tok: str | None) -> None:
        if not tok:
            return
        try:
            payload = decode_token(tok)
            jti = payload.get("jti") if isinstance(payload, dict) else None
            if not jti:
                return
            exists = db.scalar(select(TokenBlacklist.id).where(TokenBlacklist.jti == jti))
            if not exists:
                db.add(TokenBlacklist(jti=jti))
                db.commit()
        except Exception:
            return

    _revoke(access_token)
    _revoke(refresh_token)

    _delete_cookie_auth(response)
    return {"message": "Logout realizado com sucesso"}