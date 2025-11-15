"""
"""
from __future__ import annotations
import json
import logging

from pathlib import Path

from swfv.builder import PageBuilder
from swfv.data import FileInfo, Meta, SWFVJsonEncoder
from swfv.utils.fs import FileUtil

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from swfv.config import Config

logger = logging.getLogger()

def process_dir(work_dir: Path, config: Config, depth: int = 0) -> None:
    builder = PageBuilder(config=config)
    _process_dir(work_dir, config, depth, builder)
    builder.copy_assets()

def _process_dir(work_dir: Path, config: Config, depth: int, builder: PageBuilder) -> Meta:
    tab = "." * depth
    try:
        work_dir = Path(work_dir)
        work_dir_rel = work_dir.relative_to(config.source)
        output_dir = config.output / work_dir_rel
        logger.info(f"{tab}Processing {work_dir_rel} to {output_dir} (level={depth})...")
        # thumbnail_dir = output_dir / config.thumbs_dir
        meta = Meta(path=work_dir_rel,
                    output_file_path = output_dir / config.meta_file,
                    depth=depth,
                    thumbnail_path=Path(config.thumbs_dir))
        for p in FileUtil.search(work_dir):
            if p.name.startswith(".") or \
                p.name.startswith("__") or \
                    (depth == 0 and p.name == config.assets_dir):
                continue
            if p.is_dir():
                dir_meta = _process_dir(p, config, depth + 1, builder)
                fi = FileInfo(path=p)
                fi.size = dir_meta.size
                meta.directories.append(fi)
                meta.size += fi.size
            elif p.name not in (config.hash_file, config.meta_file, config.index_file):
                logger.info(f"{tab}> File: {p.relative_to(config.source)}")
                fi = FileInfo(path=p)
                meta.files.append(fi)
                meta.size += fi.size
        meta.directories.sort(key=lambda x:x.name)
        meta.files.sort(key=lambda x:x.name)
        # print(f"META ({meta.output_file_path}) = {meta}")
        logger.info(f"{tab}Create meta file: {meta.output_file_path}")
        meta.output_file_path.parent.mkdir(parents=True, exist_ok=True)
        with meta.output_file_path.open("wt") as writer:
            json.dump(meta.to_dict(), fp=writer, indent=2, cls=SWFVJsonEncoder)
        index_file_path = meta.output_file_path.parent / config.index_file
        logger.info(f"{tab}Create index file: {index_file_path}")
        builder.create_index_file(meta, index_file_path, force=config.force)
        hash_file = meta.output_file_path.parent / config.hash_file
        if meta.files:
            logger.info(f"{tab}Create hash file: {hash_file}")
            with hash_file.open("wt") as writer:
                for fi in meta.files:
                    writer.write(f"{fi.hash}  {fi.name}\n")
        return meta

    finally:
        logger.info(f"{tab}Process {work_dir} (level={depth}) finished")
