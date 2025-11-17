"""
"""
from __future__ import annotations
from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from swfv.config import Config
from swfv.data import FileType
from swfv.utils.common import HashUtil
from swfv.utils.fs import FileUtil

if TYPE_CHECKING:
    from swfv.data import FileInfo, Meta

logger = logging.getLogger()

STARTED = datetime.now(tz=timezone.utc)
STARTED_ISO = STARTED.isoformat()[:19]
STARTED_ID = STARTED.strftime("%y%m%d%H%M%S")


@dataclass
class PageItem:
    name: str = ""
    path: str = ""
    path_orig: str = ""
    icon: str = ""
    size: str = ""
    type: str = ""
    is_file: bool = False
    created: str = ""
    modified: str = ""
    origin: FileInfo | None = None

    @staticmethod
    def from_file_info(file_info: FileInfo, meta: Meta) -> PageItem:
        if file_info.type != FileType.LINK:
            path = f"./{file_info.name}"
        else:
            path = FileUtil.read_url_file(file_info.path_real)

        item = PageItem(
            name=file_info.name,
            path=path,
            path_orig=file_info.name,
            icon=f"{'../' * meta.depth}assets/icons/{file_info.thumbnail_sm}",
            size=FileUtil.size_format(file_info.size),
            type=file_info.type.value.lower(),
            created=file_info.created.isoformat(sep=" ")[:19],
            modified=file_info.modified.isoformat(sep=" ")[:19],
        )
        item.is_file = item.type in FileType.values() and item.type != FileType.DIRECTORY.value
        return item


class PageBuilder:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.theme_path = Path(config.theme)
        if not self.theme_path.exists():
            self.theme_path = Config.APP_DIR / "themes" / config.theme
        logger.info(f"Use theme: {self.theme_path}")
        if not self.theme_path.exists():
            raise OSError(f"Theme not found: {self.theme_path}")
        self.hash_util = HashUtil(self.config.APP_NAME)
        self.engine = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.theme_path.absolute()),
            autoescape=True)

    def create_index_file(self, meta: Meta, output_file: Path, force: bool = False) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if not force and output_file.exists():
            raise OSError(f"File exists: {output_file}")
        page_tmpl = self.engine.get_template("page.j2")
        items: list[PageItem] = []
        total_hash: list[str] = []
        if meta.depth > 0:
            item = PageItem(
                name="..", path="..",
                icon=f"{'../' * meta.depth}assets/icons/back.png",
                size="-", type="go back",
                created="-", modified="-")
            logger.debug(f"ITEM: {item}")
            items.append(item)
        for p in meta.directories:
            item = PageItem.from_file_info(p, meta=meta)
            logger.debug(f"ITEM: {item}")
            items.append(item)
            total_hash.append(p.name)
        for p in meta.files:
            item = PageItem.from_file_info(p, meta=meta)
            logger.debug(f"ITEM: {item}")
            items.append(item)
            total_hash.append(p.hash)

        dir_count = len(meta.directories)
        file_count = len(meta.files)
        page_hash = self.hash_util.get_hash("".join(total_hash))
        page_size = FileUtil.size_format(meta.size, round=True)
        page_id = f"{page_hash[:8]}-d{dir_count}f{file_count}-{page_size.lower()[:-1]}"
        path = "" if str(meta.path) in ("/", ".") else str(meta.path)
        page_content = page_tmpl.render({
            "title": f"{self.config.name}: {path}" if path else self.config.name,
            "config": self.config,
            "items": items,
            "path": str(Path("/") / path),
            "relpath": "./" + "../" * meta.depth,
            "app_name": self.config.APP_NAME,
            "app_version": self.config.APP_VERSION,
            "name": self.config.name,
            "display_name": self.config.display_name,
            "datetime_iso": STARTED_ISO,
            "datetime_ts": int(STARTED.timestamp()),
            "hash": page_hash,
            "page_id": page_id,
            "path_size": meta.size,
            "path_size_fmt": page_size,
        })
        output_file.open("w").write(page_content)
        logger.info(f"Write file: {output_file}")

    def copy_assets(self) -> None:
        src = self.theme_path / self.config.assets_dir
        dest = self.config.output / self.config.assets_dir
        logger.info(f"Copy assets directory: {src}")
        FileUtil.copy(src, dest)
