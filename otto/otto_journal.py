
import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Data path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FILE_PATH = DATA_DIR / "otto_journal.json"

# -------------------- Low-level utils --------------------

def _write_json(data) -> None:
    tmp = FILE_PATH.with_suffix(FILE_PATH.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE_PATH)

def _migrate_list_to_dict(items):
    # Convert legacy list-of-dicts into a dict keyed by timestamp
    migrated = {}
    for item in items or []:
        if isinstance(item, dict):
            ts = item.get("timestamp") or item.get("time") or item.get("ts")
            if not ts:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            key = ts
            i = 1
            while key in migrated:
                key = f"{ts}_{i}"
                i += 1
            migrated[key] = {k: v for k, v in item.items() if k not in {"timestamp", "time", "ts"}}
    return migrated

def _parse_ts(ts: str) -> datetime:
    # Try several formats, default to now() to avoid crashes
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            pass
    # If it has suffix like _2 from migration, strip it and retry
    if "_" in ts:
        return _parse_ts(ts.split("_", 1)[0])
    return datetime.now()

def _entries_sorted(journal: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], datetime]]:
    items = []
    for ts, entry in journal.items():
        if not isinstance(entry, dict):
            continue
        items.append((ts, entry, _parse_ts(ts)))
    items.sort(key=lambda x: x[2], reverse=True)
    return items

# -------------------- Storage API --------------------

def load_journal() -> Dict[str, Any]:
    if FILE_PATH.exists():
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    # Normalize to dict
    if isinstance(data, list):
        data = _migrate_list_to_dict(data)
        _write_json(data)
    elif not isinstance(data, dict):
        data = {}
        _write_json(data)

    return data

def save_journal(entries: Dict[str, Any]) -> None:
    if isinstance(entries, list):
        entries = _migrate_list_to_dict(entries)
    elif not isinstance(entries, dict):
        entries = {}
    _write_json(entries)

# -------------------- High-level helpers --------------------

def write_to_journal(name: str, text: str, *, emotion: Optional[str] = None, tags: Optional[List[str]] = None) -> None:
    journal = load_journal()
    if not isinstance(journal, dict):
        journal = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    journal[timestamp] = {
        "name": name,
        "text": text,
    }
    if emotion:
        journal[timestamp]["emotion"] = emotion
    if tags:
        journal[timestamp]["tags"] = tags
    save_journal(journal)

def _format_entry(ts: str, entry: Dict[str, Any]) -> str:
    # e.g., "2025-09-17 11:45 — <name>: <text>"
    n = entry.get("name") or ""
    t = entry.get("text") or ""
    return f"{ts} — {n}: {t}" if n else f"{ts} — {t}"

def get_last_entries(limit: int = 5, user: Optional[str] = None) -> List[str]:
    j = load_journal()
    out = []
    for ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        out.append(_format_entry(ts, entry))
        if len(out) >= limit:
            break
    return out

def get_entries_about(topic: str, limit: int = 10, user: Optional[str] = None) -> List[str]:
    topic_l = (topic or "").lower()
    if not topic_l:
        return []
    j = load_journal()
    out = []
    for ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        text = str(entry.get("text",""))
        if topic_l in text.lower():
            out.append(_format_entry(ts, entry))
            if len(out) >= limit:
                break
    return out

def get_best_memory(user: Optional[str] = None) -> Optional[str]:
    # Heuristic: pick the most positive-looking recent entry
    positives = ["harika", "mükemmel", "başardım", "mutlu", "süper", "iyi his", "gurur"]
    j = load_journal()
    for ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        text = str(entry.get("text",""))
        if any(p in text.lower() for p in positives):
            return _format_entry(ts, entry)
    # fallback: return most recent
    for ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        return _format_entry(ts, entry)
    return None

def summarize_today(user: Optional[str] = None) -> str:
    j = load_journal()
    today = date.today()
    todays = []
    for ts, entry, dt in _entries_sorted(j):
        if dt.date() != today:
            continue
        if user and entry.get("name") != user:
            continue
        todays.append(entry)
    if not todays:
        return "Bugün için günlük kaydı yok."
    last_text = todays[0].get("text","")
    return f"Bugün {len(todays)} kayıt var. En sonuncusu: {last_text}"

def get_important_memories(user: Optional[str] = None, limit: int = 5) -> List[str]:
    # Heuristic: lines containing 'önemli', 'kritik', 'hedef' or '!' are important.
    j = load_journal()
    marked = []
    fallback = []
    for ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        text = str(entry.get("text",""))
        if any(k in text.lower() for k in ["önemli", "kritik", "hedef"]) or "!" in text:
            marked.append(_format_entry(ts, entry))
        else:
            fallback.append(_format_entry(ts, entry))
    out = (marked[:limit] if marked else fallback[:limit])
    return out

def get_last_emotion_for_user(user: str) -> Optional[str]:
    j = load_journal()
    for _ts, entry, _dt in _entries_sorted(j):
        if entry.get("name") == user and "emotion" in entry:
            return entry.get("emotion")
    return None

def needs_goal_review(user: Optional[str] = None) -> bool:
    # If there's any 'hedef' entry in the last 7 items without 'tamamlandı', suggest review.
    j = load_journal()
    cnt = 0
    for _ts, entry, _dt in _entries_sorted(j):
        if user and entry.get("name") != user:
            continue
        text = str(entry.get("text","")).lower()
        if "hedef" in text and "tamamlandı" not in text and "bitti" not in text:
            return True
        cnt += 1
        if cnt >= 7:
            break
    return False
