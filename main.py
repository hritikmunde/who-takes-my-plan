"""Who Takes My Plan — voice agent for finding in-network doctors.

Run with `guava run .` from the project directory.
"""

import logging

import guava
from guava import logging_utils

from src.providers import lookup, KNOWN_PLANS

logger = logging.getLogger("who_takes_my_plan")

agent = guava.Agent(
    purpose=(
        "Help elderly callers find an in-network doctor or hospital that "
        "matches their insurance plan and their medical need."
    ),
)


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)
    call.set_task(
        "find_provider",
        objective=(
            "Find an in-network doctor matching the caller's plan and need. "
            "The caller may be elderly and on phone audio, possibly with "
            "hearing aids: use short sentences, speak clearly, and be patient "
            "if asked to repeat or slow down."
        ),
        checklist=[
            guava.Say(
                "Hi, I can help you find an in-network doctor. This will "
                "just take a moment."
            ),
            guava.Field(
                key="plan",
                field_type="multiple_choice",
                choices=KNOWN_PLANS,
                description="Which insurance plan do they have?",
            ),
            "Confirm back the plan you heard before moving on.",
            guava.Field(
                key="need",
                field_type="text",
                description=(
                    "What kind of doctor do they need, or what body part "
                    "hurts? Accept plain language like 'my knees hurt' or "
                    "'my eyes', not just clinical terms."
                ),
            ),
            "Confirm back what you heard before moving on.",
            guava.Field(
                key="city",
                field_type="text",
                description="What city or area are they in?",
            ),
            "If the caller asks you to repeat something or speak slower at "
            "any point during this call, do so patiently.",
        ],
    )


@agent.on_task_complete("find_provider")
def on_find_provider_complete(call: guava.Call):
    plan = call.get_field("plan")
    need = call.get_field("need")
    city = call.get_field("city")
    logger.info("Looking up: plan=%r need=%r city=%r", plan, need, city)

    matches = lookup(plan, need, city)

    if matches:
        top = matches[:3]
        listing = "; ".join(
            f"{p['name']}, {p['specialty']}, at {p['address']} in {p['city']}, "
            f"phone {p['phone']}"
            for p in top
        )
        call.send_instruction(
            f"Tell the caller you found {len(top)} matching doctor(s): "
            f"{listing}. Speak slowly, one at a time. Read every phone "
            f"number digit by digit, with pauses. Only use the names, "
            f"addresses, and phone numbers given here — never invent or "
            f"guess any detail."
        )
    else:
        logger.info("No match for plan=%r need=%r city=%r", plan, need, city)
        call.send_instruction(
            "Tell the caller plainly that no in-network doctor was found "
            "matching their plan and need. Do not guess or suggest a doctor "
            "that wasn't given to you. Suggest they call their plan's "
            "member services line for more options."
        )

    call.set_task(
        "wrap_up",
        objective="Offer to repeat the information, then close the call warmly.",
        checklist=[
            "Ask if they'd like anything repeated.",
            "Ask if there's anything else you can help with.",
            "Once they're done, thank them for calling and say goodbye warmly.",
        ],
    )


@agent.on_task_complete("wrap_up")
def on_wrap_up_complete(call: guava.Call):
    logger.info("Wrap-up complete (session: %s)", call.id)
    call.hangup()


@agent.on_question
def on_question(call: guava.Call, question: str) -> str:
    logger.info("Question received: %s", question)
    return (
        "I can only help with finding an in-network doctor or hospital "
        "for your plan. For other questions, please call the member "
        "services number on your insurance card."
    )


@agent.on_session_end
def on_session_end(call: guava.Call, event):
    logger.info("Session ended (session: %s)", call.id)


if __name__ == "__main__":
    logging_utils.configure_logging()

    # Run this to talk to your agent using your local audio device.
    # agent.call_local()

    # Run this to attach your agent to a phone number. Call your agent's number to talk to it.
    agent.listen_phone("+14843175018")

    # Run this to receive a WebRTC link where you can talk to your agent in the browser.
    # agent.listen_webrtc()

    # Run this to test your agent in a text-based chat session in the terminal (no audio required).
    # agent.chat()
