
import json
import os

FILE_PATH = 'data/user_memory.json'

def load_user_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "rules": {}}

def save_user_data(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_behavior_rule(user_id, rule_type, value):
    data = load_user_data()
    if "rules" not in data:
        data["rules"] = {}
    if user_id not in data["rules"]:
        data["rules"][user_id] = []

    rule = {rule_type: value}
    if rule not in data["rules"][user_id]:
        data["rules"][user_id].append(rule)
        save_user_data(data)
        return True
    return False

def get_behavior_rules(user_id):
    data = load_user_data()
    return data.get("rules", {}).get(user_id, [])

def interpret_emotion_response(user_id, user_emotion):
    rules = get_behavior_rules(user_id)
    for rule in rules:
        if "when_user_is" in rule and rule["when_user_is"] == user_emotion:
            return rule.get("respond_like", None)
        if "always_respond" in rule:
            return rule["always_respond"]
    return None
