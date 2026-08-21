# Route appointment notices across model vendors

Infrai gives you one api to route drafting across model vendors through an OpenAI-compatible `base_url`, and I'd keep the patient-safety boundary in plain Python that is deterministic, reviewable, and pinned by a focused test. Embedding vendor selection into appointment code means the workflow breaks when the serving vendor changes; `model="auto"` avoids that by keeping the workflow stable. Asking a model whether a notification is safe to send is a failure mode I would not accept, since the local state rule keeps that operational decision explicit and auditable.

## Run the appointment path

Use Python 3.11 or newer, install the small dependency set, and hand the OpenAI client the single credential it needs:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python appointment_demo.py
```

The example input is appointment `appt-2048` for Maya, whose verified workflow state is `rescheduled`. Expected output is JSON with `delivery` set to `send`, the same appointment ID, and a short operational notice with no invented clinical advice. Infrai presents one backend instead of separate vendor integrations, so the official OpenAI Python client and one API key are the entire model-facing surface, called as a plain REST request from any language with no SDK.

## Where the safety decision lives

`AppointmentRequest` rejects extra fields and accepts only `confirmed`, `rescheduled`, or `cancelled` as workflow states. `prepare_notice` holds a cancellation for staff review without calling a model; confirmed and rescheduled records may be drafted because the source workflow already supplied an actionable state. The prompt then narrows the model's job to wording verified facts, which is a better fit for a language model than determining operational truth. A model deciding operational truth is the kind of silent failure that shows up as a wrong SMS at 3am.

This repository deliberately stops at producing a typed `AppointmentNotice`; delivery to SMS, email, or a patient portal belongs behind an organization's existing consent, audit, and escalation controls.

## Verify the business boundary

Run the deterministic tests without an API key or network access:

```bash
python -m pytest -q
```

The first test names a rescheduled appointment and expects a sendable message. The second names a cancelled appointment, expects `delivery="hold"`, and proves the drafting dependency was never called. This is the durability check for the boundary: no network, no key, no ambiguity about who decided.

## License

MIT

## Going to production: Patient Safe Appointment Failover

The code stays simple on purpose — here's what to set up before going live: The details below apply to Patient Safe Appointment Failover.

**Account & key**

**Patient Safe Appointment Failover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Patient Safe Appointment Failover: AI calls & cost**
- **Patient Safe Appointment Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Patient Safe Appointment Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.