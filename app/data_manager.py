import json
import os
from app.config import CONFIG


def load_cards():
    try:
        with open(CONFIG["data"]["cards_file"], encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_collection():
    collection_file = CONFIG["data"]["collection_file"]
    if os.path.exists(collection_file):
        try:
            with open(collection_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_collection(collection):
    with open(CONFIG["data"]["collection_file"], 'w') as f:
        json.dump(collection, f, indent=2)
