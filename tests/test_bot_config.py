import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bot.config import resolve_model, DEFAULT_MODEL_KEY


def test_resolve_model_valid():
    deep, quick = resolve_model("gpt-5.1")
    assert deep == "gpt-5.1"
    assert quick == "gpt-5.1"


def test_resolve_model_default_on_invalid():
    deep, quick = resolve_model("not-a-model")
    assert deep == quick == resolve_model(DEFAULT_MODEL_KEY)[0]
