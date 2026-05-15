import uuid
from ninja import Schema
from pydantic import EmailStr


class LoginInput(Schema):
    email: EmailStr
    password: str


class UserOut(Schema):
    id: uuid.UUID
    email: str
    full_name: str
    role: str


class LoginOut(Schema):
    user: UserOut
    message: str


class MessageOut(Schema):
    message: str
