"""
"""
from __future__ import annotations
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from swfv.config import Config

def cleanup(work_dir: Path, config: Config) -> int:     # noqa: PLR0912, PLR0915, C901
    err_code = 0
    print(f"Collect all directories to deletion in {work_dir}...")
    dirs = list(work_dir.rglob(pattern=config.thumbs_dir))
    dirs.append(work_dir / config.assets_dir)
    print(f"Found {len(dirs)} directories.")
    print(f"Collect all files to deletion in {work_dir}...")
    files = list(work_dir.rglob(pattern=config.meta_file))
    files.extend(list(work_dir.rglob(pattern=config.hash_file)))
    files.extend(list(work_dir.rglob(pattern=config.index_file)))
    print(f"Found {len(files)} files.")
    if not dirs and not files:
        print("There are nothing do delete. Exit.")
        return 0

    print("Paths which will be deleted:")
    for p in dirs:
        print(f"[DIR ] {p}")
    for p in files:
        print(f"[FILE] {p}")
    print(f"There are {len(dirs)} directories and {len(files)} files will be deleted.")
    answer = (input(f"Do you really want to cleanup in '{work_dir}' (y/N)? ") or "No").lower().strip()
    if answer not in ("yes", "y"):
        print(f"Answer is '{answer}'. Exit.")
        return 1
    for p in dirs:
        try:
            if not p.exists():
                continue
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink()
            print(f"[DIR ] {p} - DELETED")
        except OSError as ex:
            err_code += 1
            print(f"[FILE] {p} - delete failed: {ex}")
    for p in files:
        try:
            if not p.exists():
                continue
            need_to_delete = False
            if p.name == config.index_file:
                check_line = "generated on"
                with p.open("r") as reader:
                    for line in reader.readlines():
                        if check_line in line.lower():
                            need_to_delete = True
                            break
            else:
                need_to_delete = True
            if need_to_delete:
                p.unlink(missing_ok=True)
            print(f"[FILE] {p} - DELETED ({str(need_to_delete).lower()})")
        except OSError as ex:
            err_code += 1
            print(f"[FILE] {p} - delete failed: {ex}")
    if err_code:
        print(f"Cleanup was failed: {err_code} errors.")
    else:
        print("Cleanup was successfull")
    return err_code
