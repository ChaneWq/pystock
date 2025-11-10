# storage.py
import json
from typing import List, Dict
from pathlib import Path

TASKS_FILE = "tasks.json"


def load_tasks() -> List[Dict]:
    path = Path(TASKS_FILE)
    if not path.exists():
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    return tasks

def save_tasks(tasks: List[Dict]) -> None:
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
