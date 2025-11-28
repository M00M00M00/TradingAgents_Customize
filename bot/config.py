from typing import Tuple

ALLOWED_MODELS = {
    "gpt-5.1": ("gpt-5.1", "gpt-5.1"),
    "gpt-5-mini": ("gpt-5-mini", "gpt-5-mini"),
    "gpt-5-nano": ("gpt-5-nano", "gpt-5-nano"),
    "o4-mini": ("o4-mini", "o4-mini"),
    "gpt-4.1-mini": ("gpt-4.1-mini", "gpt-4.1-mini"),
}

DEFAULT_MODEL_KEY = "gpt-5-mini"


def resolve_model(key: str | None) -> Tuple[str, str]:
    """
    Map a user-provided model key to (deep_think_llm, quick_think_llm).
    Falls back to DEFAULT_MODEL_KEY if the key is invalid or None.
    """
    if key and key in ALLOWED_MODELS:
        return ALLOWED_MODELS[key]
    return ALLOWED_MODELS[DEFAULT_MODEL_KEY]
