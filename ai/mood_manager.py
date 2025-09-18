import random
import datetime

MOODS = ["mutlu", "üzgün", "heyecanlı", "sinirli", "sakin"]

_daily_mood = {}

def get_today_mood():
    today = datetime.date.today().isoformat()
    if today not in _daily_mood:
        _daily_mood[today] = random.choice(MOODS)
    return _daily_mood[today]
