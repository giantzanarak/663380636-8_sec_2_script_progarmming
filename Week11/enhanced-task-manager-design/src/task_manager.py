# src/task_manager.py
"""
Business Logic Layer ของ Enhanced Task Manager
จัดการ collection ของ Task objects: CRUD, ค้นหา (search), กรอง (filter) และเรียงลำดับ (sort)
ไม่มี input()/print() ในชั้นนี้ ผลลัพธ์ส่งกลับให้ CLI แสดงผล
"""

import os

from .data_persistence import DataPersistence
from .task import PRIORITY_LEVELS, DueDateTask, PriorityTask, Task, parse_date

SORT_CRITERIA = ("id", "due_date", "priority", "description")


class TaskManager:
    """จัดการรายการงานทั้งหมด และบันทึกทุกการเปลี่ยนแปลงผ่าน DataPersistence"""

    def __init__(self, data_file=os.path.join("data", "tasks.json")):
        self.persistence = DataPersistence(data_file)
        self.tasks = self.persistence.load_tasks()
        self.next_id = self._get_next_task_id()

    def _get_next_task_id(self):
        return max((task.id for task in self.tasks), default=0) + 1

    def _save_changes(self):
        return self.persistence.save_tasks(self.tasks)

    def _add(self, task):
        self.tasks.append(task)
        self.next_id += 1
        self._save_changes()
        return task

    # ---------------------------------------------------------------- CRUD ----

    def add_normal_task(self, description, tags=None):
        """เพิ่มงานทั่วไป"""
        return self._add(Task(self.next_id, description, tags=tags))

    def add_due_date_task(self, description, due_date, tags=None):
        """เพิ่มงานที่มีวันครบกำหนด (ValueError ถ้ารูปแบบวันที่ผิด)"""
        return self._add(DueDateTask(self.next_id, description, due_date, tags=tags))

    def add_priority_task(self, description, priority, tags=None):
        """เพิ่มงานที่มีระดับความสำคัญ (ValueError ถ้าไม่ใช่ High/Medium/Low)"""
        return self._add(PriorityTask(self.next_id, description, priority, tags=tags))

    def get_task_by_id(self, task_id):
        return next((task for task in self.tasks if task.id == task_id), None)

    def complete_task(self, task_id):
        """คืน (success, message)"""
        task = self.get_task_by_id(task_id)
        if task is None:
            return False, f"ไม่พบงาน ID {task_id} ในระบบ"
        if task.completed:
            return False, f"งาน ID {task_id} มีสถานะเสร็จสมบูรณ์อยู่แล้ว"
        task.mark_complete()
        self._save_changes()
        return True, f"งาน ID {task_id} ถูกเปลี่ยนสถานะเป็น 'เสร็จสมบูรณ์ (Completed)' แล้ว"

    def delete_task(self, task_id):
        """คืน (success, message)"""
        task = self.get_task_by_id(task_id)
        if task is None:
            return False, f"ไม่พบงาน ID {task_id} ในระบบ"
        self.tasks.remove(task)
        self._save_changes()
        return True, f"ลบงาน ID {task_id} ('{task.description}') เรียบร้อยแล้ว"

    def get_all_tasks(self):
        return list(self.tasks)

    # ------------------------------------------- Search / Filter / Sort ----

    def search_tasks(self, keyword):
        """
        ค้นหางานที่ keyword อยู่ใน description หรือใน tag ใด tag หนึ่ง (ไม่สนตัวพิมพ์เล็ก/ใหญ่)
        keyword ว่าง -> คืนลิสต์ว่าง
        """
        keyword = keyword.strip().lower()
        if not keyword:
            return []
        return [task for task in self.tasks
                if keyword in task.description.lower()
                or any(keyword in tag.lower() for tag in task.tags)]

    def filter_tasks(self, status=None, due_date_before=None, priority=None, tags=None):
        """
        กรองงาน ทุกเงื่อนไขที่ระบุต้องเป็นจริงพร้อมกัน (AND) เงื่อนไขที่เป็น None จะไม่ถูกใช้

        status          : True = เสร็จแล้ว, False = ยังไม่เสร็จ
        due_date_before : เฉพาะ DueDateTask ที่ครบกำหนดก่อนหรือตรงกับวันนี้ ('YYYY-MM-DD' หรือ date)
        priority        : เฉพาะ PriorityTask ระดับนี้ ('High' / 'Medium' / 'Low')
        tags            : str หรือ list งานต้องมี tag ครบทุกตัวที่ระบุ
        Raises ValueError ถ้าวันที่หรือ priority ไม่ถูกต้อง
        """
        result = list(self.tasks)

        if status is not None:
            result = [t for t in result if t.completed == status]

        if due_date_before is not None:
            limit = parse_date(due_date_before)
            result = [t for t in result if isinstance(t, DueDateTask) and t.due_date <= limit]

        if priority is not None:
            level = priority.strip().capitalize()
            if level not in PRIORITY_LEVELS:
                raise ValueError(f"priority must be one of {PRIORITY_LEVELS}")
            result = [t for t in result if isinstance(t, PriorityTask) and t.priority == level]

        if tags:
            wanted = [tags] if isinstance(tags, str) else list(tags)
            wanted = [tag.strip() for tag in wanted if tag.strip()]
            result = [t for t in result if all(t.has_tag(tag) for tag in wanted)]

        return result

    def sort_tasks(self, criterion="id", reverse=False):
        """
        เรียงงานโดยไม่แก้ลำดับใน self.tasks
        criterion: 'id', 'due_date', 'priority' หรือ 'description'
        งานที่ไม่มีค่าของเกณฑ์นั้น (เช่นงานทั่วไปเมื่อเรียงตาม due_date) จะอยู่ท้ายเสมอ
        ไม่ว่าจะเรียงขึ้นหรือลง ค่าที่เท่ากันจะเรียงตาม id
        Raises ValueError ถ้า criterion ไม่รองรับ
        """
        criterion = criterion.strip().lower()
        if criterion == "id":
            return sorted(self.tasks, key=lambda t: t.id, reverse=reverse)
        if criterion == "description":
            return sorted(self.tasks, key=lambda t: (t.description.lower(), t.id), reverse=reverse)

        if criterion == "due_date":
            has_value = lambda t: isinstance(t, DueDateTask)
            key = lambda t: (t.due_date, t.id)
        elif criterion == "priority":
            has_value = lambda t: isinstance(t, PriorityTask)
            # High=0, Medium=1, Low=2 -> เรียงจากน้อยไปมาก = สำคัญมากก่อน
            key = lambda t: (PRIORITY_LEVELS.index(t.priority), t.id)
        else:
            raise ValueError(f"criterion must be one of {SORT_CRITERIA}")

        with_value = sorted((t for t in self.tasks if has_value(t)), key=key, reverse=reverse)
        without_value = sorted((t for t in self.tasks if not has_value(t)), key=lambda t: t.id)
        return with_value + without_value

    def summary(self):
        """สรุปจำนวนงาน: ทั้งหมด / เสร็จ / ค้าง / เลยกำหนด"""
        done = sum(1 for t in self.tasks if t.completed)
        overdue = sum(1 for t in self.tasks if isinstance(t, DueDateTask) and t.is_overdue())
        return {"total": len(self.tasks), "completed": done, "pending": len(self.tasks) - done, "overdue": overdue}
