# main.py
"""
Entry point of the Enhanced Task Manager.

Usage:
    python main.py            # normal run; log written to logs/task_manager.log
    python main.py --debug    # also print debug log lines in the terminal
"""

import argparse
import logging
import os
import sys

from src.cli_interface import CLIInterface
from src.task_manager import TaskManager

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "task_manager.log")


def setup_logging(debug=False):
    """
    INFO and above go to logs/task_manager.log; only warnings are shown in the terminal
    (all levels with --debug), so log lines do not clutter the menu.
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler],
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Enhanced Task Manager CLI")
    parser.add_argument("--debug", action="store_true", help="show debug log messages in the terminal")
    args = parser.parse_args()

    # Thai/UTF-8 text on the Windows console
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    setup_logging(args.debug)
    CLIInterface(TaskManager()).run()


if __name__ == "__main__":
    main()
