# storage.py
import json
from typing import List, Dict
from config import TASKS_FILE

def load_tasks() -> List[Dict]:
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        tasks = []
    return tasks

def save_tasks(tasks: List[Dict]) -> None:
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

