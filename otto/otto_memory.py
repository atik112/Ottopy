
import json
import os
import random

FILE_PATH = 'data/otto_memories.json'

def load_memories():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memories(memories):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def get_memory_about(name):
    memories = load_memories()
    if name in memories and memories[name]:
        return random.choice(memories[name])
    return None

def add_memory_about(name, memory):
    memories = load_memories()
    if name not in memories:
        memories[name] = []
    if memory not in memories[name]:
        memories[name].append(memory)
        save_memories(memories)
