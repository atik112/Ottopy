from pathlib import Path
import json, pickle

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
ASSETS_SOUNDS = PACKAGE_ROOT / "assets" / "sounds"

def ensure_runtime_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_SOUNDS.mkdir(parents=True, exist_ok=True)

    # JSON files with defaults
    defaults = {
        DATA_DIR / "user_memory.json": {"users": {}},
        DATA_DIR / "otto_memories.json": {},
        DATA_DIR / "otto_journal.json": [],
        DATA_DIR / "mood_state.json": {"mood": "neutral"},
    }
    for path, default in defaults.items():
        if not path.exists():
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")

    # face_data.pkl
    face_pkl = DATA_DIR / "face_data.pkl"
    if not face_pkl.exists():
        with open(face_pkl, "wb") as f:
            pickle.dump({}, f)
