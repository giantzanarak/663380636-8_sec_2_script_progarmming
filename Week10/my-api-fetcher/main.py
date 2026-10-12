"""
main.py
โปรแกรมหลัก Interactive CLI สำหรับทดสอบการเชื่อมต่อ Web API
สัปดาห์ที่ 10: Interacting with Web APIs: Fetching and Processing JSON Data
"""

import sys
from typing import Optional

from src.api_client import APIClient

# ให้ Windows Console แสดงภาษาไทยและ Emoji ได้
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POSTS_DISPLAY_LIMIT = 5


def display_menu() -> None:
    """แสดงเมนูตัวเลือกการทำงานของโปรแกรม"""
    print("\n" + "=" * 45)
    print("   🌐 Web API Data Fetcher CLI (Week 10)")
    print("=" * 45)
    print("  1. ดึงข้อมูลงานเดี่ยว (Fetch Single TODO)")
    print("  2. ดึงรายการโพสต์ทั้งหมด (Fetch All Posts)")
    print("  3. ดึงรายการ TODO ตามรหัสผู้ใช้ (Fetch User TODOs)")
    print("  4. ออกจากโปรแกรม (Exit)")
    print("=" * 45)


def read_positive_int(prompt: str, name: str) -> Optional[int]:
    """รับตัวเลขจำนวนเต็มบวกจากผู้ใช้ คืน None (พร้อมแจ้งข้อผิดพลาด) ถ้าป้อนไม่ถูกต้อง"""
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError:
        print(f"❌ ข้อผิดพลาด: '{raw}' ไม่ใช่ตัวเลขที่ถูกต้อง กรุณาป้อนเฉพาะตัวเลขจำนวนเต็ม")
        return None
    if value <= 0:
        print(f"❌ ข้อผิดพลาด: {name} ต้องเป็นตัวเลขจำนวนเต็มบวกที่มากกว่า 0")
        return None
    return value


def handle_fetch_single_todo(client: APIClient) -> None:
    """1. ดึงและแสดง TODO รายการเดียวตาม ID"""
    todo_id = read_positive_int("กรุณาป้อนรหัส TODO ID ที่ต้องการค้นหา (เช่น 1, 5, 10): ", "TODO ID")
    if todo_id is None:
        return

    todo = client.fetch_single_todo(todo_id)
    if not todo:
        print(f"⚠️ ไม่พบข้อมูล TODO สำหรับ ID: {todo_id}")
        return

    status = "เสร็จสิ้น (Completed) ✅" if todo.get("completed") else "รอดำเนินการ (Pending) ⏳"
    print("\n📋 --- ข้อมูลงาน TODO รายการเดี่ยว ---")
    print(f"  • รหัสงาน (ID)              : {todo.get('id')}")
    print(f"  • รหัสผู้รับผิดชอบ (User ID): {todo.get('userId')}")
    print(f"  • หัวข้องาน (Title)         : {todo.get('title')}")
    print(f"  • สถานะงาน (Status)         : {status}")
    print("-" * 45)


def _user_sort_key(item):
    """Sorts user IDs numerically (1, 2, ..., 10); anything that is not an int goes last."""
    user_id = item[0]
    return (0, user_id, "") if isinstance(user_id, int) else (1, 0, str(user_id))


def handle_fetch_all_posts(client: APIClient) -> None:
    """2. ดึงโพสต์ทั้งหมด แสดง 5 รายการแรก พร้อมสรุปจำนวนโพสต์ต่อผู้ใช้"""
    posts = client.fetch_all_posts()
    if posts is None:
        print("⚠️ ไม่สามารถดึงรายการโพสต์ได้ในขณะนี้")
        return
    if not posts:
        print("ℹ️ ไม่มีโพสต์ในระบบ")
        return

    total = len(posts)
    print(f"\n📝 --- แสดง {min(POSTS_DISPLAY_LIMIT, total)} รายการแรก (จากทั้งหมด {total} รายการ) ---")
    for index, post in enumerate(posts[:POSTS_DISPLAY_LIMIT], start=1):
        body = (post.get("body") or "").replace("\n", " ")
        print(f"\n[{index}] Post ID: {post.get('id')} | User ID: {post.get('userId')}")
        print(f"    หัวข้อ (Title): {post.get('title')}")
        print(f"    เนื้อหา (Body) : {body[:60]}{'...' if len(body) > 60 else ''}")

    if total > POSTS_DISPLAY_LIMIT:
        print(f"\n... และยังมีอีก {total - POSTS_DISPLAY_LIMIT} โพสต์ที่ไม่ได้แสดงบนหน้าจอ")

    # ประมวลผล JSON เพิ่มเติม: นับจำนวนโพสต์ของผู้ใช้แต่ละคน
    posts_per_user = {}
    for post in posts:
        posts_per_user[post.get("userId")] = posts_per_user.get(post.get("userId"), 0) + 1
    summary = ", ".join(f"User {uid}: {count}" for uid, count in sorted(posts_per_user.items(), key=_user_sort_key))
    print(f"\n📊 จำนวนโพสต์ต่อผู้ใช้ -> {summary}")
    print("-" * 45)


def handle_fetch_user_todos(client: APIClient) -> None:
    """3. ดึง TODO ทั้งหมดของผู้ใช้ และสรุปจำนวนงานที่เสร็จ / ค้าง"""
    user_id = read_positive_int("กรุณาป้อนรหัสผู้ใช้งาน User ID (เช่น 1, 2, 3): ", "User ID")
    if user_id is None:
        return

    todos = client.fetch_user_todos(user_id)
    if todos is None:
        print(f"⚠️ เกิดข้อผิดพลาด ไม่สามารถดึงงานของ User ID {user_id} ได้")
        return
    if not todos:
        print(f"ℹ️ ไม่พบรายการงาน TODO ของ User ID {user_id}")
        return

    print(f"\n📋 --- รายการงาน TODO ทั้งหมดของ User ID {user_id} (รวม {len(todos)} รายการ) ---")
    for todo in todos:
        icon = "✅" if todo.get("completed") else "⏳"
        print(f"  [{todo.get('id', 0):03d}] {icon} {todo.get('title')}")

    completed = sum(1 for todo in todos if todo.get("completed"))
    percent = completed / len(todos) * 100
    print("-" * 45)
    print(f"สรุป: เสร็จแล้ว {completed}/{len(todos)} งาน ({percent:.0f}%) | รอดำเนินการ {len(todos) - completed} งาน")


def main() -> None:
    """ฟังก์ชันหลักในการควบคุม Flow การทำงานของโปรแกรม"""
    client = APIClient()
    handlers = {"1": handle_fetch_single_todo, "2": handle_fetch_all_posts, "3": handle_fetch_user_todos}

    try:
        while True:
            display_menu()
            choice = input("กรุณาเลือกเมนู (1-4): ").strip()
            if choice == "4":
                print("\n👋 ขอบคุณที่ใช้งานโปรแกรม ขอยุติการทำงาน!")
                break
            handler = handlers.get(choice)
            if handler:
                handler(client)
            else:
                print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาป้อนตัวเลขระหว่าง 1 ถึง 4 เท่านั้น")
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 ยุติการทำงาน")


if __name__ == "__main__":
    main()
