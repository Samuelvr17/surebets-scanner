from __future__ import annotations

import json

from src.ingestion.authorized_api_source import AuthorizedAPISource
from src.ingestion.base import OddsSource
from src.ingestion.bookmaker_source import BookmakerSource
from src.ingestion.local_snapshot_source import LocalSnapshotSource


def load_sources(config_path: str) -> list[OddsSource]:
    config = json.load(open(config_path, 'r', encoding='utf-8'))
    sources: list[OddsSource] = []
    for src in config.get('sources', []):
        if not src.get('enabled', False):
            continue
        if src['type'] == 'local_snapshot':
            sources.append(LocalSnapshotSource(src['id'], src['input_dir'], src['initial']))
        elif src['type'] == 'authorized_api':
            sources.append(AuthorizedAPISource(src['id'], src.get('base_url', ''), src.get('api_key_env')))
        elif src['type'] == 'bookmaker_adapter':
            sources.append(BookmakerSource(src['id'], src.get('bookmaker', src['id']), src.get('adapter_profile', '')))
    return sources
