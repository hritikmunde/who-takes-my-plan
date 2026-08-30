# Onboarding — Who Takes My Plan

This file is for a teammate picking up this repo mid-hackathon, likely by
feeding it to their own Claude Code session. It's factual as of **2026-08-29,
~6:30pm** — check `git log` for anything newer than what's described here.

## What this is

**Who Takes My Plan** is a voice agent for a hackathon. It helps elderly
callers find in-network doctors and hospitals: they call a number, say their
insurance plan and what kind of doctor they need, and hear real answers read
back slowly. No website, no portal, no login — phone only.

Built on the **Guava** voice platform (`guava-sdk`, Python). Tonight's build
window is 2 hours; see "The clock" below.

## Read `BUILD_STEPS.md` next

It's the phased build plan. Its original "Guava API" section was copied from
the hackathon's event PDF and was **wrong** in several ways — see the warning
below. It has since been corrected against what's actually installed in this
repo (commit `cdb9a36`, and a second fix in `c5c257a`). Trust the file as it
stands now, not any prior version or the event PDF.

`CLAUDE.md` is referenced by `BUILD_STEPS.md` as something that should live in
the repo root — **it does not exist as a file yet.** Its intended content
(hard rules, stack, working style) currently only lives inside a template
block in `BUILD_STEPS.md`'s Phase 0 section. See "Hard rules" below for the
substance of it.

## The real Guava API, as it exists in this repo

Verified against the installed CLI (`guava 0.40.0`) and the actual scaffold
`guava create` generated — not the event PDF's simplified example.

```python
import guava

agent = guava.Agent(
    purpose="Help callers find in-network doctors and hospitals",
)
# name/organization are NOT Agent() constructor args.
# They live in guava.toml (already set: name = "who-takes-my-plan").

@agent.on_call_start
def start(call: guava.Call):
    call.set_task(
        "find_provider",
        objective="Find an in-network doctor matching their plan and need",
        checklist=[
            guava.Field(key="plan", field_type="text", description="Which insurance plan do they have?"),
            guava.Field(key="need", field_type="text", description="What kind of doctor or what body part hurts?"),
            guava.Field(key="city", field_type="text", description="What city or area are they in?"),
        ],
    )

@agent.on_task_complete("find_provider")
def done(call: guava.Call):
    plan = call.get_field("plan")
    # ... look up, then speak the result — see send_instruction below ...
    call.hangup()
```

Key facts:
- **Entrypoint is `main.py`**, not `agent.py`. `guava run` hardcodes `uv run main.py`.
- **Run with `guava run .`** — not `python main.py` or `python agent.py`.
- `guava.Field(key, description='', question='', field_type='text', required=True, choices=[], searchable=False, sensitive=False)`
- `guava.Say("...")` — a checklist item spoken **verbatim**, for exact wording.
- Checklist items are `Field | Say | str` (a plain string is a freeform instruction the LLM follows in its own words).
- **To speak something computed at runtime** (e.g. reading back a doctor's address you just looked up), use `call.send_instruction(instruction: str)` — *not* `Say` (that's for text known ahead of time) and *not* a return value (return values are only for `on_question`/`on_action_request`, answering something the caller asked).

## ⚠️ Warning: don't trust the original BUILD_STEPS.md API section

The first version of `BUILD_STEPS.md`'s "Guava API" section was transcribed
from the event's PDF handout, not the real SDK. It got several things wrong:
`guava.Agent(name=, organization=, purpose=)` (real signature only takes
`purpose`), `agent.py` as the entrypoint (real entrypoint is `main.py`), and
`guava.Field("key", "description")` as positional args (real signature is
keyword-only: `key=`, `description=`, etc.). It also implied `call_local()`
rings your actual phone — it doesn't (see below).

All of this has been corrected in the current `BUILD_STEPS.md` (commits
`cdb9a36`, `c5c257a`). If your own knowledge or a cached memory of "the Guava
API" disagrees with what's in this repo right now, **the repo is right.**

## Phase status (with evidence — not just checkbox state)

`BUILD_STEPS.md`'s Phase 0 checkboxes are still unchecked in the file even
though most of that phase is actually done. Go by this instead:

- **Phase 0 — mostly done.** Guava CLI installed, `guava login` completed,
  `guava create --direction inbound` run, scaffold pushed to GitHub. Repo is
  public with two collaborators besides the owner (`shamika2504`,
  `swamini-21`, both write access) — confirmed via `gh api
  repos/hritikmunde/who-takes-my-plan/collaborators`.
  **Not done:** `CLAUDE.md` does not exist as a file in the repo root.
- **Phase 1 — ✅ done, eligibility confirmed.** `main.py` now runs
  `agent.listen_phone("+14843175018")` (commit `edf07df`). The run log shows
  a real PSTN call: accepted from an outside number, a question asked and
  answered, clean `user-hangup`. This satisfies the hackathon's "must place
  or answer at least one live call" rule. Marked done in `BUILD_STEPS.md`,
  commit `244202a`.
- **Phase 2 (provider data) — not started.** No `data/` or `src/` directory
  exists in the repo.
- **Phase 3 (real call flow) — not started.** `main.py` still runs the stock
  scaffold `guava create` generated: an "intro" task that greets the caller
  and answers questions about Guava itself via RAG over `guava-docs.md`. It
  is **not** the provider-finder agent yet — no `find_provider` task, no
  checklist for plan/need/city, no lookup wiring.
- **Phase 4 (technical complexity) and freeze prep — not started.**

## Setup on a fresh machine

1. Install the Guava CLI (macOS): `brew install goguava-ai/tap/guava`, then
   `guava --version` to confirm (this repo was built against `0.40.0`).
2. `guava login` — **your own account.** This opens a browser; you have to
   click through it yourself, an AI agent can't.
3. `git clone` this repo, `cd who-takes-my-plan`.
4. `guava run .` — this uses `uv` and will resolve dependencies from the
   committed `pyproject.toml`/`uv.lock` automatically.

**Important — you likely can't run the live phone number.** The project in
`guava.toml` (`project_id`, `org_id`) and the provisioned number
(`+1 484-317-5018`) belong to hritikmunde's Guava account/org. Logging in
with your own Guava account does **not** automatically give you access to
this project — if `guava run .` or `guava numbers list` errors on
permissions, you need to be added as a member of that org on the Guava
dashboard first.

Even once you have access: **only one process can hold the `listen_phone()`
listener on that number at a time.** If hritikmunde already has `guava run .`
running live against `+14843175018`, don't also run `listen_phone()` against
it — coordinate first. For your own iteration, use `agent.chat()` (terminal
text) or `agent.call_local()` (local mic/speakers) instead — both work
independently per-machine and don't touch the shared number.

## Hard rules (the substance of the not-yet-created CLAUDE.md)

- **Never invent a provider name, address, or phone number.** Read only from
  `data/providers.json` once it exists (Phase 2). A hallucinated doctor is a
  demo-killing failure.
- Callers are elderly, on phone audio, possibly with hearing aids: short
  sentences, confirm back what you heard before moving on, speak numbers
  slowly.
- If nothing matches, say so plainly. Never pad with a guess.
- Every result spoken must include: name, specialty, address, phone.
- 2-hour hackathon: prefer working code over clean code. Do one phase of
  `BUILD_STEPS.md` at a time. Don't add dependencies without asking. Don't
  refactor working code unless asked.

## The clock

| Time | What |
|---|---|
| 6:30 | Build starts — **2 hours only** |
| 8:30 | **Code freeze.** Judging begins immediately: 3 judges, 2 min demo + 1 min Q&A each |
| 9:30 | Top five present |

Anything not done by 8:25 does not exist. See `BUILD_STEPS.md` for the cut
list if you're running out of time.
