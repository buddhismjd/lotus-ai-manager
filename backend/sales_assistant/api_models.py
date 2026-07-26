from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_MESSAGE_LENGTH = 4000
MAX_SESSION_ID_LENGTH = 128
MAX_SESSION_TOKEN_LENGTH = 128
SESSION_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
SESSION_TOKEN_PATTERN = r"^[A-Za-z0-9_-]{32,128}$"
_SESSION_ID_RE = re.compile(SESSION_ID_PATTERN)
_SESSION_TOKEN_RE = re.compile(SESSION_TOKEN_PATTERN)


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def normalize_session_token(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("session_token must be a string")
    normalized = value.strip()
    if len(normalized) > MAX_SESSION_TOKEN_LENGTH or not _SESSION_TOKEN_RE.fullmatch(normalized):
        raise ValueError("session_token has an invalid format")
    return normalized


class SalesChatRequest(StrictRequestModel):
    message: Annotated[str, Field(max_length=MAX_MESSAGE_LENGTH)] = ""
    session_id: Annotated[str, Field(max_length=MAX_SESSION_ID_LENGTH)] = "default"
    session_token: Annotated[str | None, Field(max_length=MAX_SESSION_TOKEN_LENGTH)] = None

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValueError("message must be a string")
        return value.strip()

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: object) -> str:
        if value is None:
            return "default"
        if not isinstance(value, str):
            raise ValueError("session_id must be a string")
        normalized = value.strip() or "default"
        if len(normalized) > MAX_SESSION_ID_LENGTH or not _SESSION_ID_RE.fullmatch(normalized):
            raise ValueError("session_id has an invalid format")
        return normalized

    @field_validator("session_token", mode="before")
    @classmethod
    def validate_session_token(cls, value: object) -> str | None:
        return normalize_session_token(value)


class SalesResetRequest(StrictRequestModel):
    session_id: Annotated[str, Field(max_length=MAX_SESSION_ID_LENGTH)] = "default"
    session_token: Annotated[str | None, Field(max_length=MAX_SESSION_TOKEN_LENGTH)] = None

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: object) -> str:
        return SalesChatRequest.normalize_session_id(value)

    @field_validator("session_token", mode="before")
    @classmethod
    def validate_session_token(cls, value: object) -> str | None:
        return normalize_session_token(value)

class SalesRotateTokenRequest(SalesResetRequest):
    pass
