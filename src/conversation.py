import re

# Captures 1-3 consecutive Capitalized words right after "in"/"to"/"at" —
# e.g. "in San Jose", "to Riverside". Requiring capitalization is what keeps
# this from false-positiving on ordinary phrases like "have to pay" or "in
# general", where the word after in/to/at isn't a proper noun.
_CITY_MENTION = re.compile(r"\b(?:in|to|at)\s+((?:[A-Z][A-Za-z'-]*\s*){1,3})")


def extract_city_change(question: str) -> str | None:
    """Best-effort extraction of a city name from a caller's follow-up
    question about searching a different city, e.g. "what about in San Jose"
    or "can you check the city to San Francisco". Returns None if no
    capitalized place-name-shaped phrase trails an "in"/"to"/"at".
    """
    if not question:
        return None
    text = question.strip().rstrip("?.!")
    mentions = list(_CITY_MENTION.finditer(text))
    if not mentions:
        return None

    # The mention closest to the end of the sentence is the most likely
    # actual city reference (earlier "in"/"to" often belongs to other
    # phrasing that happens to precede the real one, e.g. "change the city
    # to San Francisco").
    return mentions[-1].group(1).strip()
