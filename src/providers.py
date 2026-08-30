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
    "neurology": ["headache", "head hurt", "head pain", "migraine", "seizure", "numbness", "nerve", "neuro"],
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


def lookup_with_status(plan: str, need: str, city: str = "") -> tuple[list[dict], bool]:
    """Find providers matching plan + need, preferring the given city.

    Returns (matches, city_matched). `city_matched` is True when the
    returned providers are actually in the requested city (or no city was
    given), and False when they're a "nearest alternative" fallback from a
    different city on the same plan+specialty — important to disclose
    since two towns with the same name (or a city not in this dataset at
    all) shouldn't be silently presented as exact matches.
    """
    specialty = map_specialty(need)
    if specialty is None:
        return [], True

    matches = [
        p for p in PROVIDERS
        if p["specialty"] == specialty and _plan_matches(plan, p["accepted_plans"])
    ]

    if not city:
        return matches, True

    city_norm = city.strip().lower()
    city_matches = [p for p in matches if p["city"].strip().lower() == city_norm]
    if city_matches:
        return city_matches, True

    return matches, False


def lookup(plan: str, need: str, city: str = "") -> list[dict]:
    """Find providers matching plan + need, preferring the given city.

    See lookup_with_status() for the city-fallback semantics this wraps.
    """
    matches, _ = lookup_with_status(plan, need, city)
    return matches
