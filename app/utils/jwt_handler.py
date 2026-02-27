from __future__ import annotations

import os
import uuid
import datetime as dt
from typing import Any, Dict, Optional

from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def criar_token(payload: Dict[str, Any], expires_in: int) -> str:
    """
    expires_in: minutos (mantendo o padrão do seu código)
    """
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=int(expires_in))

    data = dict(payload or {})
    data.setdefault("jti", str(uuid.uuid4()))
    data["iat"] = int(now.timestamp())
    data["exp"] = int(exp.timestamp())

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida assinatura e expiração.
    Retorna payload (dict) ou None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not isinstance(payload, dict):
            return None
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica SEM validar expiração (útil para logout -> extrair jti).
    Ainda valida assinatura (por padrão).
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        if not isinstance(payload, dict):
            return None
        return payload
    except JWTError:
        return None