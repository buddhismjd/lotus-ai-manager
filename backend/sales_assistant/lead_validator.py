from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_TELEGRAM_PATTERN = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")


class LeadContactChannel(StrEnum):
    TELEGRAM = "telegram"
    MAX = "max"


class LeadValidationCode(StrEnum):
    NAME_REQUIRED = "name_required"
    NAME_TOO_SHORT = "name_too_short"
    CONTACT_CHANNEL_REQUIRED = "contact_channel_required"
    CONTACT_CHANNEL_UNSUPPORTED = "contact_channel_unsupported"
    CONTACT_VALUE_REQUIRED = "contact_value_required"
    CONTACT_VALUE_INVALID = "contact_value_invalid"
    EMAIL_REQUIRED = "email_required"
    EMAIL_INVALID = "email_invalid"


@dataclass(frozen=True, slots=True)
class LeadValidationError:
    field: str
    code: LeadValidationCode
    message: str


@dataclass(frozen=True, slots=True)
class LeadContactData:
    name: str
    contact_channel: LeadContactChannel
    contact_value: str
    email: str


@dataclass(frozen=True, slots=True)
class LeadValidationResult:
    data: LeadContactData | None
    errors: tuple[LeadValidationError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.data is not None and not self.errors


class LeadValidator:
    """Validate the mandatory contact contract for manager handoff."""

    def validate(
        self,
        *,
        name: str | None,
        contact_channel: str | LeadContactChannel | None,
        contact_value: str | None,
        email: str | None,
    ) -> LeadValidationResult:
        errors: list[LeadValidationError] = []

        clean_name = self._clean(name)
        if not clean_name:
            errors.append(
                LeadValidationError(
                    "name",
                    LeadValidationCode.NAME_REQUIRED,
                    "Укажите, пожалуйста, Ваше имя.",
                )
            )
        elif len(clean_name) < 2:
            errors.append(
                LeadValidationError(
                    "name",
                    LeadValidationCode.NAME_TOO_SHORT,
                    "Имя должно содержать не менее двух символов.",
                )
            )

        channel = self._parse_channel(contact_channel)
        if contact_channel is None or not str(contact_channel).strip():
            errors.append(
                LeadValidationError(
                    "contact_channel",
                    LeadValidationCode.CONTACT_CHANNEL_REQUIRED,
                    "Выберите Telegram или MAX.",
                )
            )
        elif channel is None:
            errors.append(
                LeadValidationError(
                    "contact_channel",
                    LeadValidationCode.CONTACT_CHANNEL_UNSUPPORTED,
                    "Для связи доступны Telegram или MAX.",
                )
            )

        clean_contact = self._clean(contact_value)
        if not clean_contact:
            errors.append(
                LeadValidationError(
                    "contact_value",
                    LeadValidationCode.CONTACT_VALUE_REQUIRED,
                    "Укажите контакт для связи.",
                )
            )
        elif channel is not None and not self._valid_contact(channel, clean_contact):
            errors.append(
                LeadValidationError(
                    "contact_value",
                    LeadValidationCode.CONTACT_VALUE_INVALID,
                    self._contact_error_message(channel),
                )
            )

        clean_email = self._clean(email).lower()
        if not clean_email:
            errors.append(
                LeadValidationError(
                    "email",
                    LeadValidationCode.EMAIL_REQUIRED,
                    "Укажите, пожалуйста, email.",
                )
            )
        elif not _EMAIL_PATTERN.fullmatch(clean_email):
            errors.append(
                LeadValidationError(
                    "email",
                    LeadValidationCode.EMAIL_INVALID,
                    "Проверьте формат email.",
                )
            )

        if errors or channel is None:
            return LeadValidationResult(data=None, errors=tuple(errors))

        return LeadValidationResult(
            data=LeadContactData(
                name=clean_name,
                contact_channel=channel,
                contact_value=self._normalise_contact(channel, clean_contact),
                email=clean_email,
            )
        )

    @staticmethod
    def _clean(value: str | None) -> str:
        return " ".join((value or "").strip().split())

    @staticmethod
    def _parse_channel(
        value: str | LeadContactChannel | None,
    ) -> LeadContactChannel | None:
        if isinstance(value, LeadContactChannel):
            return value
        normalised = (value or "").strip().lower()
        aliases = {
            "telegram": LeadContactChannel.TELEGRAM,
            "телеграм": LeadContactChannel.TELEGRAM,
            "tg": LeadContactChannel.TELEGRAM,
            "max": LeadContactChannel.MAX,
            "макс": LeadContactChannel.MAX,
        }
        return aliases.get(normalised)

    @staticmethod
    def _valid_contact(channel: LeadContactChannel, value: str) -> bool:
        if channel == LeadContactChannel.TELEGRAM:
            return bool(_TELEGRAM_PATTERN.fullmatch(value))
        return len(value) >= 3

    @staticmethod
    def _normalise_contact(channel: LeadContactChannel, value: str) -> str:
        if channel == LeadContactChannel.TELEGRAM and not value.startswith("@"):
            return f"@{value}"
        return value

    @staticmethod
    def _contact_error_message(channel: LeadContactChannel) -> str:
        if channel == LeadContactChannel.TELEGRAM:
            return "Укажите Telegram username, например @username."
        return "Укажите корректный контакт MAX."


__all__ = [
    "LeadContactChannel",
    "LeadContactData",
    "LeadValidationCode",
    "LeadValidationError",
    "LeadValidationResult",
    "LeadValidator",
]
