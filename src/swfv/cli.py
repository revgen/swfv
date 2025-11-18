#!/usr/bin/env python
# #############################################################################
## SWFV - Simple Web File Viewer

# #############################################################################
from __future__ import annotations
import argparse
import json
import logging
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from swfv.config import Config, ConfigFlag
from swfv.core import process_dir
from swfv.extra import cleanup

logger = logging.getLogger()


def _start_http_server(webroot: Path) -> int:
    try:
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        host = "localhost"
        port = int(os.environ.get("HTTP_PORT", "8080"))
        os.chdir(webroot.absolute())
        print(f"Working directory:{Path.cwd()} ")
        line_length = 80
        print("*" * line_length)
        print("*", "!!! WARNING !!!".center(line_length - 4), "*")
        print("*", f"Web server was started: http://{host}:{port}".center(line_length - 4), "*")
        print("*" * line_length)
        httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def run_cli(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(f"Simple web file viewer service.{os.linesep}"
        "A static-site generator that builds HTML pages with a file index, "
        "enabling users to navigate directories, preview files in the browser, and download them via HTTP."),
        epilog=f"{Config.APP_NAME} v{Config.APP_VERSION} {Config.APP_URL}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", default=str(Path.cwd()), nargs="?",
                        help="Path to the directory that serves as the input for indexing and page generation (default: current)")
    parser.add_argument("--output", "-o", default="",
                        help="Path to the directory used as the destination for all generated site content. (default: <source>)")
    parser.add_argument("--debug", "-D", action="store_true",
                        default=os.environ.get("DEBUG", "").lower().strip() in ("true", "on"),
                        help="Show more verbose log output")
    # parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--name", "-n", default=Config.APP_NAME,
                        help=f"Specifies the short name assigned to the generated static site (default: {Config.APP_NAME})")
    parser.add_argument("--display-name", "-d", default=Config.APP_NAME,
                        help=f"Specifies the dysplay name assigned to the generated static site (default: {Config.APP_NAME})")
    parser.add_argument("--quiet", "-Q", action="store_true",
                        help="Do not show a confirmation prompt")
    parser.add_argument("--force", "-F", action="store_true",
                        help="Force overwrite of index.html files in the destination directory")
    parser.add_argument("--cleanup", "-C", action="store_true",
                        help="Cleanup in the desctination directory, remove all generated files")
    parser.add_argument("--serve", "-S", action="store_true",
                        help="Starts a basic HTTP server that serves files from the destination directory.")
    parser.add_argument("--version", "-v", action="store_true",
                        help="Displays the current version of the tool")
    parser.add_argument("--theme", "-T", default="default",
                        help="Specifies the directory containing a custom theme (default: embedded theme)")
    possible_flags = ",".join(sorted(ConfigFlag.values()))
    parser.add_argument("--flag", "-f",
                        help=f"Extra options to fine-tune the output of the generated pages: {possible_flags}")
    pargs = parser.parse_args(args or sys.argv[1:])
    if pargs.debug:
        logger.setLevel(logging.DEBUG)
        args_print = {k: getattr(pargs, k) for k in dir(pargs) if not k.startswith("_")}
        logger.debug(f"Arguments: {json.dumps(args_print)}")

    if pargs.version:
        print(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        return 0

    logger.info(f"Start {Config.APP_NAME} v{Config.APP_VERSION}")
    cfg = Config(source=pargs.source,
                output=pargs.output,
                recursive=True, # pargs.recursive,
                name=pargs.name,
                display_name=pargs.display_name,
                quiet=pargs.quiet,
                force=pargs.force,
                theme=pargs.theme,
                flags=[v.strip().lower() for v in (pargs.flag or "").split(",") if v])
    logger.debug(f"Configuration: {cfg}")
    if pargs.cleanup:
        return cleanup(cfg.output, config=cfg)

    if pargs.serve or str(pargs.source).lower().strip() in ("serve", "server"):
        return _start_http_server(cfg.output)

    if not cfg.quiet:
        answer = (input(f"Continue in '{cfg.source}' (y/N)? ") or "No").lower().strip()
        if answer not in ("yes", "y"):
            print(f"Answer is '{answer}'. Exit.")
            return 1

    process_dir(cfg.source, config=cfg)
    return 0

def main(args: list[str] | None = None) -> int:
    try:
        logging.basicConfig(format="%(message)s", level=logging.INFO)
        return run_cli(args=args)
    except KeyboardInterrupt:
        print("")
        print("Keyboard interrupt event was received. Exit.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
