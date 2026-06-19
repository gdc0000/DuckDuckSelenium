import logging
import sys

from cli import build_parser, cmd_search, cmd_run, cmd_scrape, cmd_list, cmd_export, cmd_init
from db import init_db

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def main():
    logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT,
                        handlers=[logging.FileHandler("search.log", mode="a")])

    init_db()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    dispatch = {
        "search": cmd_search,
        "run": cmd_run,
        "scrape": cmd_scrape,
        "list": cmd_list,
        "export": cmd_export,
        "init": cmd_init,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)


if __name__ == "__main__":
    main()
