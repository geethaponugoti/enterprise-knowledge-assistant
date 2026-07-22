import json
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "chat_history.json"


def load_messages() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))


def save_messages(messages: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(messages, indent=2), encoding="utf-8")


def clear_messages() -> None:
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
