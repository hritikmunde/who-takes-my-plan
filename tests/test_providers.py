"""Quick sanity tests for src/providers.py. Run with: python tests/test_providers.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.providers import (
    lookup,
    lookup_with_status,
    map_specialty,
    PROVIDERS,
    KNOWN_PLANS,
    KNOWN_SPECIALTIES,
)

# 23 entries, correct known plans/specialties, and a state + 5-digit zipcode on every record.
assert len(PROVIDERS) == 23, f"expected 23 providers, got {len(PROVIDERS)}"
for p in PROVIDERS:
    assert p["specialty"] in KNOWN_SPECIALTIES, p["specialty"]
    for plan in p["accepted_plans"]:
        assert plan in KNOWN_PLANS, plan
    assert p["state"], p["name"]
    assert p["zipcode"].isdigit() and len(p["zipcode"]) == 5, p["name"]

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

# Zipcode lookup: exact zip not required, same 3-digit prefix counts as local.
# Dr. Linda Chen (Springfield, zip 62701) matches Medicare Advantage + primary care.
# 62709 is a different Springfield zip (same "627" prefix) with no exact provider there.
zip_matches = lookup("Medicare Advantage", "checkup", "62709")
assert len(zip_matches) >= 1, zip_matches
assert all(m["zipcode"][:3] == "627" for m in zip_matches), zip_matches

# A zip prefix with no providers at all should fall back to all plan+specialty matches,
# same as the unmatched-city fallback above.
zip_fallback = lookup("Medicare Advantage", "checkup", "99999")
assert len(zip_fallback) >= 1, "zip fallback should return plan+specialty matches"

# The deliberate zero-match case: Kaiser Senior Advantage + neurology.
no_match = lookup("Kaiser Senior Advantage", "bad headaches", "")
assert no_match == [], f"expected zero matches, got {no_match}"

# Unrecognized need should return no matches, not guess.
assert lookup("Medicare Advantage", "gibberish nonsense", "") == []

# Regression: "head hurts" (not just "headache") must map to neurology.
assert map_specialty("my head hurts really bad") == "neurology"

# lookup_with_status: exact city match -> city_matched=True.
matches, city_matched = lookup_with_status("Medicare Advantage", "checkup", "Springfield")
assert len(matches) >= 1 and city_matched is True

# lookup_with_status: exact zip prefix match -> city_matched=True too.
matches, city_matched = lookup_with_status("Medicare Advantage", "checkup", "62709")
assert len(matches) >= 1 and city_matched is True

# lookup_with_status: city not in the dataset (e.g. a real city like "San
# Jose" that two towns could share the name of) -> falls back to
# plan+specialty matches, but must say so via city_matched=False. This is
# the "don't silently claim a match in the caller's exact city" guarantee.
matches, city_matched = lookup_with_status("Medicare Advantage", "checkup", "San Jose")
assert len(matches) >= 1 and city_matched is False

# lookup_with_status: zip prefix with no providers -> same fallback disclosure.
matches, city_matched = lookup_with_status("Medicare Advantage", "checkup", "99999")
assert len(matches) >= 1 and city_matched is False

# lookup_with_status: no city given at all -> not a "mismatch", just no
# preference, so city_matched=True (nothing to disclose).
matches, city_matched = lookup_with_status("Medicare Advantage", "checkup", "")
assert len(matches) >= 1 and city_matched is True

# lookup_with_status: true zero-match case (Kaiser Senior Advantage +
# neurology) -> empty matches regardless of city_matched value.
matches, city_matched = lookup_with_status("Kaiser Senior Advantage", "bad headaches", "Chicago")
assert matches == []

# lookup() and lookup_with_status() must agree on the match list itself.
for plan, need, city in [
    ("Medicare Advantage", "checkup", "Springfield"),
    ("Medicare Advantage", "checkup", "62709"),
    ("Medicare Advantage", "checkup", "San Jose"),
    ("Kaiser Senior Advantage", "bad headaches", "Chicago"),
]:
    assert lookup(plan, need, city) == lookup_with_status(plan, need, city)[0]

print("All provider lookup tests passed.")
