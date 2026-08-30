"""Quick sanity tests for src/providers.py. Run with: python tests/test_providers.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.providers import lookup, map_specialty, PROVIDERS, KNOWN_PLANS, KNOWN_SPECIALTIES

# 20 entries, correct known plans/specialties.
assert len(PROVIDERS) == 20, f"expected 20 providers, got {len(PROVIDERS)}"
for p in PROVIDERS:
    assert p["specialty"] in KNOWN_SPECIALTIES, p["specialty"]
    for plan in p["accepted_plans"]:
        assert plan in KNOWN_PLANS, plan

# Plain-language mapping.
assert map_specialty("my heart has been hurting") == "cardiology"
assert map_specialty("my eyes are blurry") == "ophthalmology"
assert map_specialty("pain in my feet") == "podiatry"
assert map_specialty("my knees hurt") == "orthopedics"
assert map_specialty("my hip is sore") == "orthopedics"
assert map_specialty("just need a checkup") == "primary care"
assert map_specialty("cardiology please") == "cardiology"
assert map_specialty("gibberish nonsense") is None

# A real match: primary care, Medicare Advantage, Springfield.
matches = lookup("Medicare Advantage", "checkup", "Springfield")
assert len(matches) >= 1, matches
assert all(m["specialty"] == "primary care" for m in matches)
assert all("Medicare Advantage" in m["accepted_plans"] for m in matches)

# City fallback: a plan+specialty combo that exists, but not in a made-up city
# should fall back to all matches for that plan+specialty.
fallback = lookup("Medicare Advantage", "checkup", "Nowhereville")
assert len(fallback) >= 1, "city fallback should return plan+specialty matches"

# The deliberate zero-match case: Kaiser Senior Advantage + neurology.
no_match = lookup("Kaiser Senior Advantage", "bad headaches", "")
assert no_match == [], f"expected zero matches, got {no_match}"

# Unrecognized need should return no matches, not guess.
assert lookup("Medicare Advantage", "gibberish nonsense", "") == []

print("All provider lookup tests passed.")
