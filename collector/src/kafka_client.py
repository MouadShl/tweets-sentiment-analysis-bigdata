from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from kafka import KafkaProducer


@dataclass(frozen=True)
class KafkaTopics:
    posts: str
    comments: str


def build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(","),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda v: (v.encode("utf-8") if isinstance(v, str) else v),
        acks="all",
        linger_ms=50,
        retries=10,
    )


def send_json(
    producer: KafkaProducer,
    topic: str,
    value: Dict[str, Any],
    key: Optional[str] = None,
) -> None:
    producer.send(topic, key=(key or ""), value=value)

