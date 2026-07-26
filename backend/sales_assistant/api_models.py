from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_MESSAGE_LENGTH = 4000
MAX_SESSION_ID_LENGTH = 128
SESSION_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
_SESSION_ID_RE = re.compile(SESSION_ID_PATTERN)


class StrictRequestModel(BaseModel):
    """Base model for public API requests.

    Unknown fields are rejected so accidental or malicious payload expansion is
    not silently accepted by the public boundary.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SalesChatRequest(StrictRequestModel):
    message: Annotated[str, Field(max_length=MAX_MESSAGE_LENGTH)] = ""
    session_id: Annotated[str, Field(max_length=MAX_SESSION_ID_LENGTH)] = "default"

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


class SalesResetRequest(StrictRequestModel):
    session_id: Annotated[str, Field(max_length=MAX_SESSION_ID_LENGTH)] = "default"

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value: object) -> str:
        return SalesChatRequest.normalize_session_id(value)
