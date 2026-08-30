import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "providers.json"

KNOWN_PLANS = [
    "Medicare Advantage",
    "Blue Shield PPO",
    "Kaiser Senior Advantage",
    "Aetna Medicare",
]

KNOWN_SPECIALTIES = [
    "primary care",
    "cardiology",
    "ophthalmology",
    "orthopedics",
    "podiatry",
    "neurology",
]

# Plain-language phrase -> specialty. Checked as substrings against the
# caller's free-text "need", longest phrase first so specific phrases
# ("my hip") win over broader ones.
SPECIALTY_KEYWORDS = {
    "cardiology": ["heart", "cardio", "chest pain"],
    "ophthalmology": ["eye", "eyes", "vision", "ophthalm"],
    "podiatry": ["foot", "feet", "toe", "toes", "ankle"],
    "orthopedics": ["knee", "knees", "hip", "hips", "joint", "bone", "shoulder", "back pain", "ortho"],
    "neurology": ["headache", "migraine", "seizure", "numbness", "nerve", "neuro"],
    "primary care": ["checkup", "check-up", "check up", "physical", "general doctor", "primary care"],
}


def _load_providers() -> list[dict]:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


PROVIDERS = _load_providers()


def map_specialty(need: str) -> str | None:
    """Map a caller's plain-language need to one of the known specialties."""
    if not need:
        return None
    text = need.lower()

    # Direct specialty name mentioned.
    for specialty in KNOWN_SPECIALTIES:
        if specialty in text:
            return specialty

    # Plain-language phrase mapping, longest keyword first for specificity.
    all_keywords = [
        (keyword, specialty)
        for specialty, keywords in SPECIALTY_KEYWORDS.items()
        for keyword in keywords
    ]
    all_keywords.sort(key=lambda pair: len(pair[0]), reverse=True)
    for keyword, specialty in all_keywords:
        if keyword in text:
            return specialty

    return None


def _plan_matches(plan: str, accepted_plans: list[str]) -> bool:
    plan_norm = (plan or "").strip().lower()
    return any(plan_norm == p.strip().lower() for p in accepted_plans)


def lookup(plan: str, need: str, city: str = "") -> list[dict]:
    """Find providers matching plan + need, preferring the given city.

    Returns providers whose specialty matches `need` (via plain-language
    mapping) and whose accepted_plans includes `plan`. If `city` is given
    and there are matches in that city, only those are returned; otherwise
    all plan+specialty matches are returned regardless of city (a "nearest
    alternative" fallback for the no-exact-match case).
    """
    specialty = map_specialty(need)
    if specialty is None:
        return []

    matches = [
        p for p in PROVIDERS
        if p["specialty"] == specialty and _plan_matches(plan, p["accepted_plans"])
    ]

    if city:
        city_norm = city.strip().lower()
        city_matches = [p for p in matches if p["city"].strip().lower() == city_norm]
        if city_matches:
            return city_matches

    return matches
