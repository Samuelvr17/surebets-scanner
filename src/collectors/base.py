from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SnapshotBatch:
    dataset_name: str
    snapshots: list[dict]


class LocalSnapshotCollector:
    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def collect(self, dataset_name: str) -> SnapshotBatch:
        path = self.input_dir / f"{dataset_name}.json"
        payload = __import__('json').loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload, list):
            raise ValueError('snapshot file must contain a JSON array')
        return SnapshotBatch(dataset_name=dataset_name, snapshots=payload)
