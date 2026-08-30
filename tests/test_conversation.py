"""Tests for src/conversation.py. Run with: python tests/test_conversation.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.conversation import extract_city_change

# Real phrasing from actual call transcripts.
assert extract_city_change("Could you look for a provider in Riverside?") == "Riverside"
assert extract_city_change("Can you check for in-network doctors in San Francisco?") == "San Francisco"
assert extract_city_change("I asked it again to change the city to San Francisco") == "San Francisco"
assert extract_city_change("What about doctors in San Jose") == "San Jose"
assert extract_city_change("can you check in San Jose instead") == "San Jose"

# Trailing filler words are naturally excluded since they're lowercase.
assert extract_city_change("try that in Riverside please") == "Riverside"
assert extract_city_change("try that in Riverside now") == "Riverside"

# No city mention at all -> None, so the caller falls back to the generic
# scope message instead of guessing.
assert extract_city_change("Could you also look for something else?") is None
assert extract_city_change("") is None
assert extract_city_change(None) is None

# Regression cases: ordinary phrases containing "to"/"in" followed by a
# lowercase word must NOT be mistaken for a city (this was a real bug in an
# earlier version — "have to pay" matched as city="pay", "in general"
# matched as city="general").
assert extract_city_change("What is the copay I'll have to pay?") is None
assert extract_city_change("can you tell me more about how this whole thing works in general") is None

print("All conversation tests passed.")
