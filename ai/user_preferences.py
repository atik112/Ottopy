import json
import os

FILE_PATH = 'data/user_memory.json'

def load_user_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}}

def save_user_data(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_name_by_voice_id(voice_id):
    data = load_user_data()
    user = data["users"].get(voice_id)
    if isinstance(user, dict):
        return user.get("name")
    return user  # geri uyumluluk için

def get_user_mode(voice_id):
    data = load_user_data()
    user = data["users"].get(voice_id)
    if isinstance(user, dict):
        return user.get("mode", "samimi")
    return "samimi"

def set_user_mode(voice_id, mode):
    data = load_user_data()
    if voice_id not in data["users"]:
        data["users"][voice_id] = {}
    if isinstance(data["users"][voice_id], str):
        # geri uyumluluk için dönüştür
        data["users"][voice_id] = {"name": data["users"][voice_id]}
    data["users"][voice_id]["mode"] = mode
    save_user_data(data)

def register_new_user(voice_id, name):
    data = load_user_data()
    data["users"][voice_id] = {
        "name": name,
        "mode": "samimi"  # varsayılan
    }
    save_user_data(data)
