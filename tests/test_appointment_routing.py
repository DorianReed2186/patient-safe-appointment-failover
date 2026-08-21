from appointment_routing import AppointmentRequest, prepare_notice


class RecordingWriter:
    def __init__(self) -> None:
        self.calls = 0

    def draft(self, request: AppointmentRequest) -> str:
        self.calls += 1
        return f"{request.patient_first_name}, your appointment was rescheduled."


def test_rescheduled_appointment_produces_sendable_notice() -> None:
    writer = RecordingWriter()
    request = AppointmentRequest(
        appointment_id="appt-7",
        patient_first_name="Maya",
        clinic_name="Northside Family Clinic",
        starts_at="2026-08-20 09:30 local time",
        workflow_state="rescheduled",
    )

    notice = prepare_notice(request, writer)

    assert notice.delivery == "send"
    assert notice.message == "Maya, your appointment was rescheduled."
    assert writer.calls == 1


def test_cancelled_appointment_is_held_without_model_call() -> None:
    writer = RecordingWriter()
    request = AppointmentRequest(
        appointment_id="appt-8",
        patient_first_name="Maya",
        clinic_name="Northside Family Clinic",
        starts_at="2026-08-20 09:30 local time",
        workflow_state="cancelled",
    )

    notice = prepare_notice(request, writer)

    assert notice.delivery == "hold"
    assert notice.message is None
    assert notice.reason == "cancelled appointments require staff review"
    assert writer.calls == 0
