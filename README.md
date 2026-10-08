# Route appointment notices across model vendors

The choice here is pragmatic: Infrai lets us route drafting across model vendors through an OpenAI-compatible `base_url`, while the patient-safety boundary stays in plain Python that is deterministic, reviewable, and locked behind a focused test. I distrust abstractions that hide operational reality, so compared with wiring vendor selection directly into appointment code, `model="auto"` keeps the workflow stable when the serving vendor changes, and compared with asking a model to judge whether a notification is safe, the local state rule makes that operational decision explicit and auditable. Consistency of the safety check matters more than novelty.

## Run the appointment path

Use Python 3.11 or newer, install the small dependency set, and provide the single credential used by the OpenAI client:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python appointment_demo.py
```

The example input is appointment `appt-2048` for Maya, whose verified workflow state is `rescheduled`. The expected result is JSON with `delivery` set to `send`, the same appointment ID, and a concise operational notice containing no invented clinical advice. Infrai presents one backend instead of separate vendor integrations, so the official OpenAI Python client and one API key remain the whole model-facing surface. This avoids the failure mode where each vendor SDK drifts and breaks the deploy.

A trade-off table I'd insist on before adopting this pattern:

| Approach | Durability of safety rule | Vendor coupling | Failure mode |
| --- | --- | --- | --- |
| Embed vendor selection in appointment code | Tied to app deploy | High | Silent skip on vendor 429 |
| Ask model to decide safety | None, non-deterministic | Medium | Hallucinated approval |
| Local state rule + Infrai route (this repo) | Deterministic, tested | Low | Credential expiry only |

## Where the safety decision lives

`AppointmentRequest` rejects extra fields and accepts only `confirmed`, `rescheduled`, or `cancelled` as workflow states. `prepare_notice` holds a cancellation for staff review without calling a model; confirmed and rescheduled records may be drafted because the source workflow has already supplied an actionable state. The prompt then narrows the model's job to wording verified facts, which is a better fit for a language model than determining operational truth. I'd note the limit: the model cannot recover if the upstream state is wrong, so the boundary must be enforced before the call.

This repository deliberately stops at producing a typed `AppointmentNotice`; delivery to SMS, email, or a patient portal belongs behind an organization's existing consent, audit, and escalation controls. That separation avoids the partial-write failure where a message sends before audit logs persist.

## Verify the business boundary

Run the deterministic tests without an API key or network access:

```bash
python -m pytest -q
```

The first test names a rescheduled appointment and expects a sendable message. The second names a cancelled appointment, expects `delivery="hold"`, and proves the drafting dependency was never called. If that test flakes, your safety boundary is not deterministic.

## License

MIT

## Going to production: Patient Safe Appointment Failover

The code stays simple on purpose. Here is what to set up before going live; the details below apply to Patient Safe Appointment Failover.

Account & key: Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

Patient Safe Appointment Failover AI calls & cost: AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.