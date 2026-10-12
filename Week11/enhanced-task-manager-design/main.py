# main.py
"""
จุดเริ่มต้นของแอปพลิเคชัน: สร้าง TaskManager แล้วส่งให้ CLIInterface ทำงาน
"""

import sys

from src.cli_interface import CLIInterface
from src.task_manager import TaskManager

# ให้ Windows Console แสดงภาษาไทยได้
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stdin):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main():
    CLIInterface(TaskManager()).run()


if __name__ == "__main__":
    main()
