"""
"""
from __future__ import annotations
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Union


from swfv.utils.common import BaseJsonEncoder

logger = logging.getLogger()
__app_name__ = "swfv"
__version__ = "0.1.2"
__url__ = "http://github.com/revgen/swfv"

class ConfigFlag(Enum):
    SHOW_HIDDEN = "show-hidden"
    HIDE_GENERATED_BY = "hide-generated-by"
    HIDE_TITLE = "hide-title"

    @staticmethod
    def parse(value: str | ConfigFlag) -> ConfigFlag | None:
        logger.debug(f"ConfigFlag parsing '{value}'")
        res = None
        if value:
            if isinstance(value, ConfigFlag):
                res = value
            else:
                flag_value = str(value.strip()).upper().replace("-", "_")
                if hasattr(ConfigFlag, flag_value):
                    res = ConfigFlag[flag_value]
        if not res and value:
            raise ValueError(f"Can't find '{value}' in the flags: {ConfigFlag.values()}")
        logger.debug(f"ConfigFlag found '{value}' -> {res}")
        return res

    @staticmethod
    def values() -> list[str]:
        return sorted(flag.value for flag in ConfigFlag)

class Config:
    APP_NAME = __app_name__
    APP_VERSION = __version__
    APP_URL = __url__
    APP_DIR = Path(__file__).parent

    DEF_META_FILE = ".meta"
    DEF_HASH_FILE = ".md5"
    DEF_THUMBS_DIR = ".thumbs"
    DEF_ASSETS_DIR = "assets"
    DEF_INDEX_FILE = "index.html"

    def __init__(self,                                          # noqa: PLR0913
                 source: Union[str, Path, None] = None,
                 output: Union[str, Path, None] = None,
                 recursive: bool = False,
                 name: str = __app_name__,
                 display_name: str = __app_name__,
                 quiet: bool = False,
                 force: bool = False,
                 theme: str | None = None,
                 flags: list[str] | None = None) -> None:
        self.source = Path(source or Path.cwd())
        self.output = Path(output or self.source)
        self.recursive = recursive
        self.app_name = Config.APP_NAME
        self.name = name or Config.APP_NAME
        self.display_name = display_name or self.name
        self.meta_file = Config.DEF_META_FILE
        self.thumbs_dir = Config.DEF_THUMBS_DIR
        self.assets_dir = Config.DEF_ASSETS_DIR
        self.hash_file = Config.DEF_HASH_FILE
        self.index_file = Config.DEF_INDEX_FILE
        self.quiet = quiet
        self.force = force
        self.theme = theme or "default"

        self.flags: list[ConfigFlag] = []
        for flag in flags or []:
            parsed = ConfigFlag.parse(flag)
            if parsed and parsed not in self.flags:
                self.flags.append(parsed)

    def to_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "name": self.name,
            "display_name": self.display_name,
            "version": Config.APP_VERSION,
            "source": self.source or "",
            "output": self.output or "",
            "recursive": self.recursive,
            "meta_file": self.meta_file,
            "assets_dir": self.assets_dir,
            "hash_file": self.hash_file,
            "index_file": self.index_file,
            "quiet": self.quiet,
            "force": self.force,
            "theme": self.theme,
            "flags": [v.value for v in self.flags],
        }

    @property
    def flag_show_hidden(self) -> bool:
        return ConfigFlag.SHOW_HIDDEN in self.flags

    @property
    def flag_hide_generated_by(self) -> bool:
        return ConfigFlag.HIDE_GENERATED_BY in self.flags

    @property
    def flag_show_title(self) -> bool:
        return ConfigFlag.HIDE_TITLE in self.flags

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), cls=BaseJsonEncoder)
