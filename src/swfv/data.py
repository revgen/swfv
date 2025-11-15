"""
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
import json
import mimetypes
from typing import TYPE_CHECKING

from swfv.config import Config
from swfv.utils.common import BaseJsonEncoder, HashUtil
from swfv.utils.fs import FileType, FileUtil

if TYPE_CHECKING:
    from pathlib import Path

class SWFVJsonEncoder(BaseJsonEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, (Meta, FileInfo)):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class FileInfo:
    HASH = HashUtil(app_name=Config.APP_NAME)

    def __init__(self, path: Path) -> None:
        self._path = path
        self.file = not self._path.is_dir()
        self.name = self._path.name
        stat = self._path.stat()
        self.created = datetime.fromtimestamp(int(stat.st_ctime or 0), tz=timezone.utc)
        self.modified = datetime.fromtimestamp(int(stat.st_mtime or 0), tz=timezone.utc)
        if self.file:
            self.size = stat.st_size
            self.hash = FileInfo.HASH.get_hash_from_file(self._path)
            self.ext = self._path.suffix[1:].lower()
            self.mime = (mimetypes.guess_type(self._path)[0] or "").lower()
            self.type = FileUtil.get_file_type(path=self._path, ext=self.ext, mime=self.mime)
        else:
            self.size = 0
            self.hash = None
            self.ext = None
            self.mime = None
            self.type = FileType.DIRECTORY
        base_name = FileUtil.normilize_file_name(f"{self._path.stem}")
        self.thumbnail_sm = f"{self.type.value.lower()}.png"
        self.thumbnail_md = f"{base_name}.md.jpg"
        self.thumbnail_lg = f"{base_name}.lg.jpg"

    @property
    def path_real(self) -> Path:
        return self._path

    def to_dict(self) -> dict:
        return {
            "name": str(self.name),
            "file": self.file,
            "size": int(self.size or 0),
            "hash": self.hash,
            "ext": self.ext,
            "type": self.type,
            "mime": self.mime,
            "created": self.created,
            "modified": self.modified,
            "thumbnail": {
                "sm": self.thumbnail_sm,
                "md": self.thumbnail_md,
                "lg": self.thumbnail_lg,
            },
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), cls=SWFVJsonEncoder)

class Meta:
    def __init__(self, path: Path, output_file_path: Path, depth: int = 0,
                 thumbnail_path: Path | None = None) -> None:
        self.path = path
        self.output_file_path = output_file_path
        self.files: list[FileInfo] = []
        self.directories: list[FileInfo] = []
        self.size = 0
        self.depth = depth
        self.thumbnail_sm = None
        self.thumbnail_md = None
        self.thumbnail_lg = None
        self.thumbnail_dir = None
        if thumbnail_path:
            self.thumbnail_dir = thumbnail_path

    def is_media_directory(self) -> bool:
        total_files = len(self.files)
        total_media = 0
        for f in self.files:
            if FileType.is_media(f.type):
                total_media += 1
        return bool(total_files and total_media * 100 // total_files > 80)      # noqa: PLR2004

    def _build_thumbnail_item(self) -> dict:
        res = {}
        if self.thumbnail_dir:
            res["dir"] = str(self.thumbnail_dir)
        if self.is_media_directory():
            thumbnail_sm = self.thumbnail_sm or (self.files[0].thumbnail_sm if self.files else None)
            thumbnail_md = self.thumbnail_md or (self.files[0].thumbnail_md if self.files else None)
            thumbnail_lg = self.thumbnail_lg or (self.files[0].thumbnail_lg if self.files else None)
            if thumbnail_sm:
                res["sm"] = thumbnail_sm
            if thumbnail_md:
                res["md"] = thumbnail_md
            if thumbnail_lg:
                res["lg"] = thumbnail_lg
        return res

    def to_dict(self) -> dict:
        result = {}
        if self.path:
            result["path"] = str(self.path or ".")
        if self.depth > 0:
            result["depth"] = self.depth
        thumbnail = self._build_thumbnail_item()
        if thumbnail:
            result["thumbnail"] = dict(thumbnail)
        result["media"] = self.is_media_directory()
        if self.directories:
            result["directories"] = [d.to_dict() for d in self.directories]
        if self.files:
            result["files"] = [f.to_dict() for f in self.files]
        result["size"] = self.size
        return result

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), cls=SWFVJsonEncoder)
