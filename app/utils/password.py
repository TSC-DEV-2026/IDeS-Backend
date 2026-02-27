from __future__ import annotations

from passlib.context import CryptContext

# bcrypt é o padrão mais comum e seguro aqui
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Gera hash seguro (bcrypt) para armazenar em tb_usuario.senha_hash.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Senha inválida")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica senha (texto) contra o hash armazenado.
    """
    if not password or not password_hash:
        return False
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        return False