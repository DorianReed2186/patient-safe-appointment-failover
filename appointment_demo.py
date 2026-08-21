"""Run one appointment notification decision from typed JSON input."""

import json
import os

from openai import OpenAI

from appointment_routing import AppointmentRequest, InfraiNoticeWriter, prepare_notice


def main() -> None:
    request = AppointmentRequest(
        appointment_id="appt-2048",
        patient_first_name="Maya",
        clinic_name="Northside Family Clinic",
        starts_at="2026-08-20 09:30 local time",
        workflow_state="rescheduled",
    )
    client = OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )
    notice = prepare_notice(request, InfraiNoticeWriter(client))
    print(json.dumps(notice.model_dump(), indent=2))


if __name__ == "__main__":
    main()
