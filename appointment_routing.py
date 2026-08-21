"""Appointment workflow decisions backed by vendor-routed language models."""

from __future__ import annotations

from typing import Literal, Protocol

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


class AppointmentRequest(BaseModel):
    """Typed input accepted by the appointment workflow."""

    model_config = ConfigDict(extra="forbid")

    appointment_id: str = Field(min_length=1)
    patient_first_name: str = Field(min_length=1)
    clinic_name: str = Field(min_length=1)
    starts_at: str = Field(min_length=1)
    workflow_state: Literal["confirmed", "rescheduled", "cancelled"]


class AppointmentNotice(BaseModel):
    """Concrete, patient-facing result of the workflow."""

    appointment_id: str
    delivery: Literal["send", "hold"]
    message: str | None
    reason: str


class NoticeWriter(Protocol):
    def draft(self, request: AppointmentRequest) -> str:
        """Return a short operational message for a verified workflow state."""


class InfraiNoticeWriter:
    """Draft notices through Infrai's OpenAI-compatible vendor routing."""

    def __init__(self, client: OpenAI) -> None:
        self._client = client

    def draft(self, request: AppointmentRequest) -> str:
        response = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write one calm appointment operations notice. Use only the supplied "
                        "facts, make no medical claims, give no clinical advice, and do not add "
                        "contact details or instructions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Patient first name: {request.patient_first_name}\n"
                        f"Clinic: {request.clinic_name}\n"
                        f"Start time: {request.starts_at}\n"
                        f"Verified state: {request.workflow_state}"
                    ),
                },
            ],
        )
        message = response.choices[0].message.content
        if not message or not message.strip():
            raise ValueError("The notice draft was empty")
        return message.strip()


def prepare_notice(
    request: AppointmentRequest,
    writer: NoticeWriter,
) -> AppointmentNotice:
    """Hold cancelled appointments; draft notices for actionable states."""

    if request.workflow_state == "cancelled":
        return AppointmentNotice(
            appointment_id=request.appointment_id,
            delivery="hold",
            message=None,
            reason="cancelled appointments require staff review",
        )

    return AppointmentNotice(
        appointment_id=request.appointment_id,
        delivery="send",
        message=writer.draft(request),
        reason="workflow state is verified for notification",
    )
