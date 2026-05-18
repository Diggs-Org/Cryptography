"""Generator function library.

Functions decorated with @register are callable by name from YAML definitions.

  !rng func(args)  — function receives the RNG as its first argument;
                     each call advances the RNG state (order matters for seed parity)
  !gen func(args)  — pure function on already-resolved param values; no RNG argument

Rules:
- Registered names are immutable once referenced in a published YAML definition.
  Renaming or removing a function breaks all existing seed/URL combinations.
- !rng functions must accept `rng` as their first positional argument.
- !gen functions must not accept an `rng` argument.
"""

_REGISTRY: dict[str, callable] = {}


def register(name: str):
    def decorator(fn):
        if name in _REGISTRY:
            raise ValueError(f"Generator '{name}' is already registered")
        _REGISTRY[name] = fn
        return fn
    return decorator


def get(name: str) -> callable:
    if name not in _REGISTRY:
        raise KeyError(f"No generator registered under '{name}'")
    return _REGISTRY[name]


def all_names() -> list[str]:
    return list(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# RNG generators  (!rng — consume from the seeded RNG)
# ---------------------------------------------------------------------------

_MEETING_LOCATIONS = [
    "THE PARK AT NOON",
    "UNDER THE OLD BRIDGE",
    "BEHIND THE MILL AT DAWN",
    "THE NORTH DOCKS AT MIDNIGHT",
    "BESIDE THE CLOCK TOWER",
    "THE EAST GATE AT DUSK",
    "THE LIBRARY STEPS AT THREE",
    "THE HARBOUR AT LOW TIDE",
]


@register("meeting_location")
def meeting_location(rng) -> str:
    """Return a random meeting location string."""
    return _MEETING_LOCATIONS[int(rng() * len(_MEETING_LOCATIONS))]


@register("rand_int")
def rand_int(rng, low: int, high: int) -> int:
    """Return a random integer in [low, high] inclusive."""
    return int(rng() * (high - low + 1)) + low


@register("rand_choice")
def rand_choice(rng, items: list):
    """Return a random element from a list."""
    return items[int(rng() * len(items))]


# ---------------------------------------------------------------------------
# Pure generators  (!gen — no RNG, deterministic on inputs)
# ---------------------------------------------------------------------------

@register("identity")
def identity(value):
    """Return the value unchanged. Used to surface a param as the answer."""
    return value


@register("caesar_encode")
def caesar_encode(text: str, shift: int) -> str:
    """Shift every alphabetic character forward by `shift` positions."""
    result = []
    for ch in text.upper():
        if ch.isalpha():
            result.append(chr((ord(ch) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(ch)
    return ''.join(result)


@register("caesar_decode")
def caesar_decode(text: str, shift: int) -> str:
    """Shift every alphabetic character backward by `shift` positions."""
    return caesar_encode(text, 26 - shift)
