""" The module contains common utils, such as:
* BaseJsonEncoder
* HashUtil
"""
from __future__ import annotations
import hashlib
import json
import logging

from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Union

logger = logging.getLogger()


class BaseJsonEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, (Path, PurePath)):
            return str(obj)
        if isinstance(obj, datetime):
            if obj.tzinfo and obj.tzinfo != timezone.utc:
                return obj.isoformat(sep="T", timespec="seconds")
            return obj.isoformat(sep="T", timespec="seconds")[:19]
        return super().default(obj)


class HashUtil:
    def __init__(self, app_name: str) -> None:
        self.cache_path = Path.home() / ".cache" / app_name / "hashes"

    def get_hash_from_file(self, file: Path) -> str:
        logger.debug(f"Calculate hash for {file}")
        file_stat = file.stat()
        output_file = f"{file.stem}-{int(file_stat.st_size)}-{int(file_stat.st_mtime)}"
        output_file = self.get_hash(output_file)
        output_dir = self.cache_path / output_file[:2]
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_file = output_dir / output_file
        if cache_file.exists():
            logger.debug(f"Found hash in the cache: {cache_file}")
            hash_val = cache_file.read_text()
        else:
            hash_val = self.get_hash(file.read_bytes())
            logger.debug(f"Calculate hash and store in the cache: {cache_file}")
            cache_file.write_text(hash_val)
        logger.debug(f"Hash was calculated ({hash_val}): {file}")
        return hash_val

    def get_hash(self, data: Union[str, bytes]) -> str:
        md5 = hashlib.md5()                                         # noqa: S324
        data4hash = data if isinstance(data, bytes) else str(data).encode("utf-8")
        md5.update(data4hash)
        return md5.hexdigest().lower()
