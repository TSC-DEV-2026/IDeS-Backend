from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field, EmailStr


class PessoaIn(BaseModel):
    nome: str = Field(..., min_length=2, max_length=160)
    cpf: str = Field(..., min_length=11, max_length=11, description="Somente dígitos (11)")
    data_nascimento: date
    adm: bool = False


class UsuarioIn(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=72)


class RegisterIn(BaseModel):
    pessoa: PessoaIn
    usuario: UsuarioIn


class PessoaOut(BaseModel):
    id: int
    nome: str
    cpf: str | None
    data_nascimento: date
    adm: bool

    class Config:
        from_attributes = True


class UsuarioOut(BaseModel):
    id: int
    email: str
    pessoa_id: int

    class Config:
        from_attributes = True


class RegisterOut(BaseModel):
    pessoa: PessoaOut
    usuario: UsuarioOut


class LoginIn(BaseModel):
    usuario: str = Field(..., description="E-mail ou CPF (somente dígitos)")
    senha: str