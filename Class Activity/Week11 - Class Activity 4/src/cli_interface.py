# src/cli_interface.py
"""
Presentation Layer: แสดงเมนู รับข้อมูลจากผู้ใช้ ตรวจสอบความถูกต้อง แล้วเรียก TaskManager
ไม่มี Business Logic ในไฟล์นี้ (Separation of Concerns)
"""

from .task import PRIORITY_LEVELS, parse_date
from .task_manager import SORT_CRITERIA


class CLIInterface:
    """ส่วนติดต่อผู้ใช้ผ่าน Command Line"""

    def __init__(self, task_manager):
        self.manager = task_manager
        self.actions = {
            "1": self.add_normal_task,
            "2": self.add_due_date_task,
            "3": self.add_priority_task,
            "4": self.list_all_tasks,
            "5": self.complete_task,
            "6": self.delete_task,
            "7": self.search_tasks,
            "8": self.filter_tasks,
            "9": self.sort_tasks,
        }

    # -------------------------------------------------------------- display ----

    def display_menu(self):
        print("\n" + "=" * 45)
        print("     Enhanced Task Manager (Week 11)")
        print("=" * 45)
        print("1. เพิ่มงานทั่วไป (Add Normal Task)")
        print("2. เพิ่มงานที่มีวันครบกำหนด (Add Due Date Task)")
        print("3. เพิ่มงานที่มีระดับความสำคัญ (Add Priority Task)")
        print("4. แสดงรายการงานทั้งหมด (List All Tasks)")
        print("5. เปลี่ยนสถานะงานเป็นเสร็จสิ้น (Complete Task)")
        print("6. ลบงาน (Delete Task)")
        print("7. ค้นหางาน (Search Tasks)")
        print("8. กรองงาน (Filter Tasks)")
        print("9. เรียงลำดับงาน (Sort Tasks)")
        print("0. ออกจากโปรแกรม (Exit)")
        print("-" * 45)

    @staticmethod
    def show_tasks(title, tasks, empty_message):
        if not tasks:
            print(f"\n[แจ้งเตือน]: {empty_message}")
            return
        print(f"\n--- {title} ({len(tasks)} รายการ) ---")
        for task in tasks:
            print(f"- {task}")
        print("-" * 45)

    # ---------------------------------------------------------------- input ----

    @staticmethod
    def get_task_description():
        while True:
            description = input("กรอกรายละเอียดงาน (Description): ").strip()
            if description:
                return description
            print("ข้อผิดพลาด: รายละเอียดงานต้องไม่เป็นค่าว่าง กรุณาลองใหม่อีกครั้ง")

    @staticmethod
    def get_date(prompt, allow_empty=False):
        """รับวันที่ YYYY-MM-DD (ถามซ้ำจนกว่าจะถูกต้อง) คืน None ถ้าเว้นว่างและอนุญาต"""
        while True:
            value = input(prompt).strip()
            if not value and allow_empty:
                return None
            try:
                return parse_date(value).strftime("%Y-%m-%d")
            except ValueError:
                print("รูปแบบวันที่ไม่ถูกต้อง! กรุณาใช้รูปแบบ YYYY-MM-DD (เช่น 2026-10-31)")

    @staticmethod
    def get_priority(prompt, allow_empty=False):
        while True:
            value = input(prompt).strip().capitalize()
            if not value and allow_empty:
                return None
            if value in PRIORITY_LEVELS:
                return value
            print("ระดับความสำคัญไม่ถูกต้อง! กรุณากรอก 'High', 'Medium' หรือ 'Low'")

    @staticmethod
    def get_tags():
        raw = input("กรอกป้ายกำกับ (Tags คั่นด้วยจุลภาค เช่น work,urgent - หรือเว้นว่างได้): ").strip()
        return [tag.strip() for tag in raw.split(",") if tag.strip()]

    @staticmethod
    def get_task_id(prompt):
        raw = input(prompt).strip().lstrip("#")
        try:
            task_id = int(raw)
        except ValueError:
            print("ข้อผิดพลาด: ID ต้องเป็นตัวเลขจำนวนเต็มเท่านั้น")
            return None
        if task_id <= 0:
            print("ข้อผิดพลาด: ID ต้องเป็นจำนวนเต็มบวก")
            return None
        return task_id

    # -------------------------------------------------------------- actions ----

    def add_normal_task(self):
        task = self.manager.add_normal_task(self.get_task_description(), tags=self.get_tags())
        print(f"[สำเร็จ]: เพิ่มงานทั่วไป ID {task.id} ('{task.description}') เรียบร้อยแล้ว")

    def add_due_date_task(self):
        description = self.get_task_description()
        due_date = self.get_date("กรอกวันครบกำหนด (YYYY-MM-DD เช่น 2026-10-31): ")
        task = self.manager.add_due_date_task(description, due_date, tags=self.get_tags())
        overdue = " (วันนี้เลยกำหนดแล้ว)" if task.is_overdue() else ""
        print(f"[สำเร็จ]: เพิ่มงานครบกำหนด ID {task.id} (ครบกำหนด: {task.due_date}{overdue}) เรียบร้อยแล้ว")

    def add_priority_task(self):
        description = self.get_task_description()
        priority = self.get_priority("กรอกระดับความสำคัญ (High / Medium / Low): ")
        task = self.manager.add_priority_task(description, priority, tags=self.get_tags())
        print(f"[สำเร็จ]: เพิ่มงานความสำคัญ ID {task.id} (ระดับ: {task.priority}) เรียบร้อยแล้ว")

    def list_all_tasks(self):
        self.show_tasks("รายการงานทั้งหมด", self.manager.get_all_tasks(), "ยังไม่มีงานในระบบ")
        if self.manager.tasks:
            s = self.manager.summary()
            print(f"สรุป: เสร็จ {s['completed']}/{s['total']} | ค้าง {s['pending']} | เลยกำหนด {s['overdue']}")

    def complete_task(self):
        task_id = self.get_task_id("กรอก ID ของงานที่เสร็จสิ้น: ")
        if task_id is not None:
            success, message = self.manager.complete_task(task_id)
            print(f"{'[สำเร็จ]' if success else '[แจ้งเตือน]'}: {message}")

    def delete_task(self):
        task_id = self.get_task_id("กรอก ID ของงานที่ต้องการลบ: ")
        if task_id is None:
            return
        task = self.manager.get_task_by_id(task_id)
        if task is None:
            print(f"[แจ้งเตือน]: ไม่พบงาน ID {task_id} ในระบบ")
            return
        if input(f"ยืนยันลบงาน '{task.description}'? (y/N): ").strip().lower() in ("y", "yes"):
            success, message = self.manager.delete_task(task_id)
            print(f"{'[สำเร็จ]' if success else '[แจ้งเตือน]'}: {message}")
        else:
            print("ยกเลิกการลบ")

    def search_tasks(self):
        keyword = input("กรอกคำค้นหา (ค้นใน Description และ Tags): ").strip()
        if not keyword:
            print("ข้อผิดพลาด: กรุณากรอกคำค้นหา")
            return
        self.show_tasks(f"ผลการค้นหาสำหรับ '{keyword}'", self.manager.search_tasks(keyword),
                        f"ไม่พบงานที่ตรงกับคำค้น '{keyword}'")

    def filter_tasks(self):
        print("\nตัวเลือกการกรอง (เว้นว่าง = ไม่ใช้เงื่อนไขนั้น, ทุกเงื่อนไขต้องตรงพร้อมกัน):")
        while True:
            status_in = input("กรองตามสถานะ (completed / pending / เว้นว่าง): ").strip().lower()
            if status_in in ("", "completed", "pending"):
                break
            print("กรุณากรอก completed, pending หรือเว้นว่าง")
        status = {"completed": True, "pending": False}.get(status_in)
        due_before = self.get_date("ครบกำหนดก่อนหรือตรงกับวันที่ (YYYY-MM-DD / เว้นว่าง): ", allow_empty=True)
        priority = self.get_priority("ระดับความสำคัญ (High / Medium / Low / เว้นว่าง): ", allow_empty=True)
        tags = self.get_tags()

        results = self.manager.filter_tasks(status=status, due_date_before=due_before, priority=priority, tags=tags)
        self.show_tasks("ผลการกรองงาน", results, "ไม่พบงานที่ตรงกับเงื่อนไขการกรอง")

    def sort_tasks(self):
        while True:
            criterion = input(f"เรียงตาม ({' / '.join(SORT_CRITERIA)}) [ค่าเริ่มต้น: id]: ").strip().lower() or "id"
            if criterion in SORT_CRITERIA:
                break
            print(f"เกณฑ์ไม่ถูกต้อง! กรุณาเลือก {', '.join(SORT_CRITERIA)}")
        reverse = input("เรียงจากมากไปน้อย (Descending? y/n) [ค่าเริ่มต้น: n]: ").strip().lower() in ("y", "yes")
        order = "มากไปน้อย" if reverse else "น้อยไปมาก"
        self.show_tasks(f"รายการงานที่จัดเรียงแล้ว (เกณฑ์: {criterion}, {order})",
                        self.manager.sort_tasks(criterion, reverse), "ไม่มีรายการงานที่จะแสดงผล")

    # ----------------------------------------------------------------- loop ----

    def run(self):
        print("ยินดีต้อนรับสู่ระบบ Enhanced Task Manager!")
        try:
            while True:
                self.display_menu()
                choice = input("เลือกเมนู (0-9): ").strip()
                if choice == "0":
                    print("\nขอบคุณที่ใช้งาน Enhanced Task Manager! ลาก่อน")
                    break
                action = self.actions.get(choice)
                if action:
                    action()
                else:
                    print("ตัวเลือกไม่ถูกต้อง! กรุณากรอกหมายเลขระหว่าง 0 ถึง 9")
        except (KeyboardInterrupt, EOFError):
            # ทุกการเปลี่ยนแปลงถูกบันทึกทันทีอยู่แล้ว จึงออกได้เลย
            print("\n\nยุติการทำงาน (ข้อมูลถูกบันทึกแล้ว)")
