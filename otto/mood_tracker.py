
import json
import os
from pathlib import Path
from typing import Dict, Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FILE_PATH = DATA_DIR / "mood_state.json"

DEFAULT = {"mood": "neutral", "score": 0}

MOOD_TO_SCORE = {
    "coşkulu": 5,
    "mutlu": 3,
    "nötr": 0,
    "üzgün": -3,
    "melankolik": -5,
    "neutral": 0,
    "happy": 3,
    "sad": -3,
}

def _write_json(data: Dict[str, Any]) -> None:
    tmp = FILE_PATH.with_suffix(FILE_PATH.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE_PATH)

def load_mood() -> Dict[str, Any]:
    if FILE_PATH.exists():
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = DEFAULT.copy()
    else:
        data = DEFAULT.copy()

    # Migrate: if it's a string, convert to dict
    if isinstance(data, str):
        label = data
        score = MOOD_TO_SCORE.get(label, 0)
        data = {"mood": label, "score": score}
        _write_json(data)

    if not isinstance(data, dict):
        data = DEFAULT.copy()
        _write_json(data)

    # Ensure keys
    data.setdefault("mood", "neutral")
    data.setdefault("score", MOOD_TO_SCORE.get(data.get("mood"), 0))
    return data

def save_mood(mood: Dict[str, Any]) -> None:
    if isinstance(mood, str):
        mood = {"mood": mood, "score": MOOD_TO_SCORE.get(mood, 0)}
    if not isinstance(mood, dict):
        mood = DEFAULT.copy()
    mood.setdefault("mood", "neutral")
    mood.setdefault("score", MOOD_TO_SCORE.get(mood.get("mood"), 0))
    _write_json(mood)

def reset_mood() -> None:
    save_mood(DEFAULT.copy())

def update_mood(sentiment: str) -> None:
    data = load_mood()
    s = sentiment.lower().strip()
    # naive scoring
    if any(k in s for k in ["mutlu", "harika", "iyi", "güzel", "sev", "başar"]):
        data["score"] += 1
    elif any(k in s for k in ["üzgün", "kötü", "kızgın", "öfke", "korku", "yorgun"]):
        data["score"] -= 1
    # clamp
    data["score"] = max(-10, min(10, data["score"]))
    # label by score
    sc = data["score"]
    if sc >= 5:
        data["mood"] = "coşkulu"
    elif sc >= 2:
        data["mood"] = "mutlu"
    elif sc >= -1:
        data["mood"] = "nötr"
    elif sc >= -4:
        data["mood"] = "üzgün"
    else:
        data["mood"] = "melankolik"
    save_mood(data)

def get_current_mood() -> Dict[str, Any]:
    """Backwards-/forwards-safe: returns dict with 'mood' and 'score'."""
    return load_mood()

def get_current_mood_label() -> str:
    return load_mood().get("mood", "nötr")
