# Who Takes My Plan — Build Plan

Voice agent that helps elderly callers find in-network doctors and hospitals.
Call a number, say your plan and what kind of doctor you need, hear real answers
read back slowly. No website, no portal, no login.

---

## The clock (read this first)

| Time | What |
|---|---|
| 5:30 | Doors, check in |
| 6:00 | Kickoff, rules read out loud |
| 6:30 | **Build starts — two hours only** |
| 7:00 | Dinner comes to the table |
| 8:30 | **CODE FREEZE.** Judging begins, 3 judges, 2 min demo + 1 min Q&A |
| 9:30 | Top five present |

**You have ~2 hours of build time.** Everything in this plan is scoped to that.
Anything not done by 8:25 does not exist.

## How you're judged

Not equally weighted:
- **Functionality — heaviest.** Does it actually work?
- **Technical complexity — heaviest.** Did you take on something hard?
- Creativity, Impact, User experience — equal middle weight
- Pitch — lightest. A smooth talker should not beat a working agent.

**Implication: ship something that works and does something technically real.
Do not spend the last 30 minutes on slides.**

**Eligibility: the agent must place or answer at least one live call.**

---

## The Guava API (verified against the installed scaffold, not the event doc)

```python
import guava

agent = guava.Agent(
    purpose="Help callers find in-network doctors and hospitals",
)
# name/organization are NOT Agent() args — they live in guava.toml,
# already set by `guava create who-takes-my-plan`.

@agent.on_call_start
def start(call: guava.Call):
    call.set_task(
        "find_provider",
        objective="Find an in-network doctor matching their plan and need",
        checklist=[
            guava.Say("Hi, I can help you find an in-network doctor."),
            guava.Field(
                key="plan",
                field_type="text",
                description="Which insurance plan do they have?",
            ),
            guava.Field(
                key="need",
                field_type="text",
                description="What kind of doctor or what body part hurts?",
            ),
            guava.Field(
                key="city",
                field_type="text",
                description="What city or area are they in?",
            ),
            "Confirm back what you heard before looking anything up.",
        ],
    )

@agent.on_task_complete("find_provider")
def done(call: guava.Call):
    plan = call.get_field("plan")
    # ... look up, speak results ...
    call.hangup()

if __name__ == "__main__":
    agent.chat()          # talk to it in your terminal
    agent.call_local()    # agent calls YOUR phone  <-- fastest path to a live call
    agent.listen_phone("+1...")  # agent answers a real number
```

Entrypoint is **`main.py`** (that's what `guava create` generates and what
`guava run` hardcodes — not `agent.py`). Run it with:

```bash
guava run .
```

The last uncommented `agent.*()` call in `main.py` decides the mode.

Key concepts: **Agent → task → checklist → `on_task_complete` handler.**
Checklist items can be `guava.Field(key=, field_type=, description=, ...)`,
`guava.Say("...")` for a scripted line, or a plain string instruction. The
checklist is how you get structure without a giant prompt. Use it.

---

## Phase 0 — BEFORE YOU LEAVE HOME

Do not do this at the venue. This is the difference between building for two
hours and installing for two hours.

- [ ] `brew install goguava-ai/tap/guava`
- [ ] `guava login` — **opens a browser, you must click through this yourself.**
      Claude Code can run the command but cannot complete the browser handoff.
- [ ] `guava create` → name it `who-takes-my-plan`
- [ ] `guava run .` — confirm you can talk to the stock agent in your terminal
- [ ] In `main.py`, comment out `agent.chat()` and uncomment `agent.call_local()`,
      run again, **confirm your phone actually rings.** This is the eligibility
      gate — prove it works tonight.
- [ ] Push the scaffold to GitHub, add teammates as collaborators
- [ ] Put this file and `CLAUDE.md` in the repo root

If Homebrew fails or login fails: office hours desk at 6:30.

### CLAUDE.md — put this in the repo root

```markdown
# Who Takes My Plan

Voice agent helping elderly callers find in-network doctors and hospitals.

## Stack
- Guava voice platform. The API is documented in BUILD_STEPS.md — follow that
  shape exactly (Agent, set_task, guava.Field checklist, on_task_complete).
- Python. Everything lives in main.py plus src/ helpers.
- Mock provider data in data/providers.json. There is no live insurance API.

## Hard rules
- NEVER invent a provider name, address, or phone number. Read only from
  providers.json. A hallucinated doctor is a demo-killing failure.
- Callers are elderly, on phone audio, possibly with hearing aids. Short
  sentences. Confirm back what you heard before moving on. Speak numbers slowly.
- If nothing matches, say so plainly. Never pad with a guess.
- Every result spoken must include: name, specialty, address, phone.

## Working style
- We are in a 2-hour hackathon. Prefer working code over clean code.
- Do ONE phase of BUILD_STEPS.md at a time. Stop and report when done.
- Don't add dependencies without asking.
- Don't refactor working code unless asked.
```

---

## Phase 1 — Make it ring (6:30–6:45)

Goal: your phone rings, you talk to your agent, before anything else exists.

- [ ] `agent.call_local()`, run, answer, say hello, hang up
- [ ] `git commit -m "ringing"` immediately — this is your floor, you're now eligible
- [ ] Edit one line of the agent's purpose, rerun, call again — confirm the edit
      loop is fast

**If this isn't working by 6:50, stop and go to the office hours desk.**

---

## Phase 2 — Provider data (6:45–7:10)

Goal: something real to search.

- [ ] `data/providers.json`, 20 entries
- [ ] Fields: `name`, `specialty`, `accepted_plans[]`, `address`, `city`,
      `phone`, `accepting_new_patients`
- [ ] 4 plans: Medicare Advantage, Blue Shield PPO, Kaiser Senior Advantage,
      Aetna Medicare
- [ ] 6 specialties: primary care, cardiology, ophthalmology, orthopedics,
      podiatry, neurology
- [ ] Include one plan+specialty combo with **zero matches** — you need the
      no-match path for the demo
- [ ] `src/providers.py` with `lookup(plan, need, city)` → list of matches
- [ ] Plain-language mapping: "my heart" → cardiology, "my eyes" → ophthalmology,
      "my feet" → podiatry, "my knees"/"my hip" → orthopedics, "checkup" →
      primary care

**Claude Code prompt:**
> Read CLAUDE.md and Phase 2 of BUILD_STEPS.md. Build only that phase:
> data/providers.json and src/providers.py with the lookup function and the
> plain-language specialty mapping. Add a quick test. Don't touch main.py.

---

## Phase 3 — The real call flow (7:10–8:00)

Goal: a full useful conversation over a live call. **This is the core.**

Flow:
1. Greet, one sentence on what it does
2. Collect `plan` — confirm back what it heard
3. Collect `need` — accept plain language, not just clinical terms
4. Collect `city`
5. On task complete: look up, speak top 2–3 slowly
6. Offer to repeat
7. Close warmly

- [ ] Wire the checklist Fields to the lookup in `on_task_complete`
- [ ] Confirm-back after each field
- [ ] No-match path: say it plainly, offer nearest alternative or suggest calling
      their plan's member services
- [ ] "Can you repeat that" / "slower please"
- [ ] Read phone numbers digit by digit with pauses
- [ ] **Test over a real call, not just `agent.chat()`.** Terminal-perfect flows
      fall apart on phone audio.

**Claude Code prompt:**
> Phase 3 of BUILD_STEPS.md. Wire the checklist to src/providers.lookup and
> speak the results. Follow the elderly-caller rules in CLAUDE.md. Keep
> agent.call_local() so I can test on my phone.

---

## Phase 4 — Technical complexity play (8:00–8:20)

Technical complexity is a heaviest-weight criterion. Pick **ONE**. Only if
Phase 3 works end to end on a real call.

**A — Live availability callback (strongest signal)**
After finding a match, the agent places a *second* real outbound call to the
doctor's office to ask if they're taking new patients, then reports back.
Two live calls in one flow. A teammate on a second phone plays the front desk.
This is the one judges will remember on technical complexity.

**B — Text them the results**
Caller hangs up with the list on their phone. Small, reliable, real user value.

**C — Warm transfer to the office**
Only if Guava supports transfer — check first, don't discover this at 8:15.

- [ ] Build one. Test on a real call. Commit.

---

## 8:20–8:30 — Freeze prep

- [ ] Last commit and push. **Stop coding at 8:25.**
- [ ] README.md: what it is, who it's for, what's mocked, how to run
- [ ] Have your phone charged and ready for the live demo
- [ ] Decide who talks and who drives the call

## The 2-minute demo (rehearse it twice)

You get 3 judges, 2 minutes each, they come to you.

1. **15s — the problem.** An 80-year-old with a new plan needs a cardiologist.
   The provider directory is a PDF on a website they can't navigate. So they
   don't go.
2. **75s — live call.** Put it on speaker. Let them hear it. Include the
   no-match moment if you have time — graceful failure builds more trust than a
   demo where everything magically works.
3. **20s — the technical bit.** Whatever you built in Phase 4, and how the
   checklist architecture keeps it from inventing a doctor.
4. **10s — impact.** Plans and hospital systems pay for this. It's their
   member services line, automated.

---

## Cut list (drop in this order)

1. Phase 4 entirely → a working search agent still scores on functionality
2. City filter → return all matches for plan + specialty
3. "Repeat that" handling
4. Plain-language mapping → make them name the specialty

**Never cut:** the live call, testing over real phone audio, stopping at 8:25.

---

## Risks

| Risk | Mitigation |
|---|---|
| Install eats build time | Done at home, tonight, before you leave |
| `guava login` browser handoff fails | Pre-provisioned accounts at office hours desk |
| Agent invents a fake doctor | CLAUDE.md rule + read only from JSON + test for it |
| Works in terminal, breaks on phone | Test on real calls from Phase 3 onward, not at 8:20 |
| Scope creep into real eligibility logic | Mock data only. Not tonight. |
| Coding past the freeze | Timer at 8:20, assigned to one person |
