from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Dict


@dataclass
class State:
    # Track high-watermarks per subreddit using created_utc.
    last_post_created_utc: Dict[str, int]
    last_comment_created_utc: Dict[str, int]


def load_state(state_path: str) -> State:
    if not os.path.exists(state_path):
        return State(last_post_created_utc={}, last_comment_created_utc={})
    with open(state_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return State(
        last_post_created_utc=dict(raw.get("last_post_created_utc", {})),
        last_comment_created_utc=dict(raw.get("last_comment_created_utc", {})),
    )


def save_state(state_path: str, state: State) -> None:
    tmp = state_path + ".tmp"
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2, sort_keys=True)
    os.replace(tmp, state_path)

