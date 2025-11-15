from __future__ import annotations
import logging
import math
import shutil
from enum import Enum
from pathlib import Path
from typing import Union, TYPE_CHECKING
import urllib

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger()


class FileType(Enum):
    DIRECTORY = "directory"
    FILE = "file"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    COMPRESSED = "compressed"
    DATA = "data"
    HTML = "html"
    PDF = "pdf"
    EBOOK = "ebook"
    CODE = "code"
    SCRIPT = "script"
    TEXT = "text"
    CONFIG = "config"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"

    @classmethod
    def parse(cls, value: Union[str, FileType, None]) -> FileType:
        res = FileType.FILE
        if value is not None:
            if isinstance(value, FileType):
                res = value
            else:
                value_name = value.upper().strip()
            if hasattr(FileType, value_name):
                res = getattr(FileType, value_name)
        logger.debug(f"FileType.Parse({value}) -> {res}")
        return res

    @staticmethod
    def is_media(file_type: FileType) -> bool:
        return file_type in (FileType.IMAGE, FileType.AUDIO, FileType.VIDEO)
    
    @staticmethod
    def values() -> list[str]:
        return sorted(flag.value for flag in FileType)


class FileUtil:
    FILE_TYPES_TEXT = ("txt", "text", "html", "htm", "md", "markdown", "mkd", "rst", "ad", "asc", "asciidoc")
    FILE_TYPES_CODE = ("py", "java", "cpp", "c", "h", "pl")
    FILE_TYPES_EBOOK = ("epub", "azw", "fb2", "fb3")
    FILE_TYPES_SHELL = ("csh", "sh", "zsh")
    FILE_TYPES_CONFIG = ("yaml", "yml", "config", "cfg", "conf", "properties", "toml", "tml")
    FILE_TYPES_LINK = ("url", "link")

    @staticmethod
    def search(path: Path, pattern: str = "*", hidden: bool = False) -> Generator[Path, None, None]:
        return (p1 for p1 in path.glob(pattern=pattern) if hidden or not p1.name.startswith("."))

    @staticmethod
    def copy(src: Path, dest: Path) -> None:
        logger.debug(f"Copying {src} -> {dest}")
        shutil.copytree(str(src.absolute()), str(dest.absolute()), dirs_exist_ok=True)

    @staticmethod
    def get_file_type(path: Path, ext: str, mime: str) -> FileType:         # noqa: PLR0912, C901
        mime_parts = (mime + "/").split("/")
        mime_type = mime_parts[0].lower().strip()
        logger.debug(f"Get file type: {path} / {ext} / {mime_type}")
        file_type = FileType.FILE
        if mime_type in ("audio", "image", "video"):
            file_type = FileType.parse(mime_type)
        elif not mime_type or mime_type in {"application", "text"}:
            mime_subtype = mime_parts[1].lower().strip().replace("x-", "").replace("vnd.", "")
            if "opendocument" in mime_subtype or "document" in mime_subtype or \
                mime_subtype in ("rtf", "visio", "abiword"):
                file_type = FileType.DOCUMENT
            if "presentation" in mime_subtype or "powerpoint" in mime_subtype:
                file_type = FileType.PRESENTATION
            if "spreadsheet" in mime_subtype or "excel" in mime_subtype:
                file_type = FileType.SPREADSHEET
            if mime_subtype in ("zip", "gzip", "bzip2", "tar", "rar", "7z", "xz") or "compressed" in mime_subtype:
                file_type = FileType.COMPRESSED
            if mime_subtype in ("json",) or "+json" in mime_subtype:
                file_type = FileType.DATA
            if mime_subtype in ("xml", "xaml") or "+xml" in mime_subtype or ext in ("xml", "xslt", "xhtml"):
                file_type = FileType.DATA
            if mime_subtype in ("pdf",):
                file_type = FileType.PDF
            if ext in ("djv", "djvu"):
                file_type = FileType.PDF
            if mime_subtype in FileUtil.FILE_TYPES_EBOOK or ext in FileUtil.FILE_TYPES_EBOOK or \
                "ebook" in mime_subtype:
                file_type = FileType.EBOOK
            if mime_subtype in FileUtil.FILE_TYPES_LINK or ext in FileUtil.FILE_TYPES_LINK:
                file_type = FileType.LINK
            if mime_subtype in FileUtil.FILE_TYPES_CODE or ext in FileUtil.FILE_TYPES_CODE:
                file_type = FileType.CODE
            if mime_subtype in FileUtil.FILE_TYPES_TEXT or ext in FileUtil.FILE_TYPES_TEXT:
                file_type = FileType.TEXT
            if mime_subtype in FileUtil.FILE_TYPES_SHELL or ext in FileUtil.FILE_TYPES_SHELL:
                file_type = FileType.SCRIPT
            if mime_subtype in FileUtil.FILE_TYPES_CONFIG or ext in FileUtil.FILE_TYPES_CONFIG:
                file_type = FileType.CONFIG
            if path.name.startswith("env."):
                file_type = FileType.CONFIG
            if "Dockerfile" in path.name:
                file_type = FileType.CODE
        logger.debug(f"Get file type: {path} / {ext} / {mime_type} -> {file_type}")
        return file_type

    @staticmethod
    def normilize_file_name(file_name: str) -> str:
        # TODO: replace non ASCII to ASCII
        return (file_name or "").replace(" ", "_")

    @staticmethod
    def size_format(size_val: int, round: bool = False) -> str:     # noqa: A002
        val = int(size_val) if size_val > 0 else 0
        res_val = None
        res_unit = None
        if val > 1024 * 1024 * 1024:
            res_val = val / 1024 / 1024 / 1024
            res_unit = "GB"
        elif val > 1024 * 1024:
            res_val = val / 1024 / 1024
            res_unit = "MB"
        else:
            res_val = val / 1024
            res_unit = "KB"
        if round:
          return f"{math.ceil(res_val)}{res_unit}"
        return f"{res_val:0.2f}{res_unit}"

    @staticmethod
    def read_url_file(path: Path) -> str:
        file_size = path.stat().st_size
        url = path.name
        if file_size > 1024 * 1024:
            logger.debug(f"File is too large for url file: size={file_size}")
        else:
            with path.open("r", encoding="utf-8") as reader:
                for line in reader.readlines():
                    if line[:20].lower().replace(" ", "").startswith("url="):
                        pos = line.index("=")
                        url = line[pos + 1:].strip()
        logger.debug(f"Parse file {path.name}: url={url}")
        return url
                



def download(uri: str, output: Path) -> None:
    try:
        output_path = Path(output)
        logger.debug(f"Download '{uri}' to '{output_path}'")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(uri) as response, \
            output_path.open("wb") as writer:                       # noqa: S310
                writer.write(response.read())
        logger.debug(f"Create file '{output_path}'.")
    except OSError as ex:
        logger.debug(f"Download file '{uri}' error: {ex}")
