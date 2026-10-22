# src/task.py
"""
Data Models ของระบบ Task Manager
Task เป็นคลาสแม่ และ DueDateTask / PriorityTask สืบทอดจาก Task (Inheritance)
แต่ละคลาส override to_dict() และ _detail_parts() ของตัวเอง (Polymorphism)
"""

import datetime

DATE_FORMAT = "%Y-%m-%d"
PRIORITY_LEVELS = ["High", "Medium", "Low"]   # เรียงจากสำคัญมากไปน้อย


def parse_date(value):
    """แปลง 'YYYY-MM-DD' หรือ datetime.date เป็น datetime.date (ValueError ถ้ารูปแบบผิด)"""
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        return datetime.datetime.strptime(value.strip(), DATE_FORMAT).date()
    raise TypeError("date must be a 'YYYY-MM-DD' string or a datetime.date")


class Task:
    """คลาสพื้นฐานของงานทุกประเภท: id, description, completed, tags"""

    TYPE_NAME = "Task"

    def __init__(self, id, description, completed=False, tags=None):
        self.id = id
        self.description = description
        self.completed = completed
        self.tags = []
        for tag in tags or []:
            self.add_tag(tag)

    def mark_complete(self):
        """เปลี่ยนสถานะงานเป็นเสร็จสมบูรณ์"""
        self.completed = True

    def add_tag(self, tag):
        """เพิ่ม tag (ตัดช่องว่าง และไม่เพิ่มซ้ำ)"""
        cleaned = str(tag).strip()
        if cleaned and cleaned not in self.tags:
            self.tags.append(cleaned)

    def remove_tag(self, tag):
        """ลบ tag ออกจากงาน (ถ้ามี)"""
        cleaned = str(tag).strip()
        if cleaned in self.tags:
            self.tags.remove(cleaned)

    def has_tag(self, tag):
        """ตรวจว่ามี tag นี้หรือไม่ (ไม่สนตัวพิมพ์เล็ก/ใหญ่)"""
        return tag.strip().lower() in (t.lower() for t in self.tags)

    def to_dict(self):
        """แปลงเป็น dict สำหรับบันทึก JSON โดยระบุ '_type' เพื่อใช้สร้าง object กลับตอนโหลด"""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
            "tags": list(self.tags),
            "_type": self.TYPE_NAME,
        }

    def _detail_parts(self):
        """ข้อมูลเฉพาะของงานแต่ละประเภท (คลาสลูก override เพื่อเพิ่ม Due / Priority)"""
        return []

    def __str__(self):
        status = "Completed" if self.completed else "Pending"
        parts = [f"ID: {self.id}", f"Description: {self.description}", f"Status: {status}"]
        parts += self._detail_parts()
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        return " | ".join(parts)

    def __repr__(self):
        return (f"{self.TYPE_NAME}(id={self.id}, description='{self.description}', "
                f"completed={self.completed}, tags={self.tags})")


class DueDateTask(Task):
    """งานที่มีวันครบกำหนด (due_date เก็บเป็น datetime.date)"""

    TYPE_NAME = "DueDateTask"

    def __init__(self, id, description, due_date, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        self.due_date = parse_date(due_date)

    def is_overdue(self, today=None):
        """เลยกำหนดแล้วและยังไม่เสร็จ"""
        return not self.completed and self.due_date < (today or datetime.date.today())

    def to_dict(self):
        data = super().to_dict()
        data["due_date"] = self.due_date.strftime(DATE_FORMAT)
        return data

    def _detail_parts(self):
        due = f"Due: {self.due_date.strftime(DATE_FORMAT)}"
        return [due + (" (OVERDUE)" if self.is_overdue() else "")]

    def __repr__(self):
        return (f"DueDateTask(id={self.id}, description='{self.description}', "
                f"due_date='{self.due_date.strftime(DATE_FORMAT)}', completed={self.completed}, tags={self.tags})")


class PriorityTask(Task):
    """งานที่มีระดับความสำคัญ High / Medium / Low"""

    TYPE_NAME = "PriorityTask"

    def __init__(self, id, description, priority, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        priority = str(priority).strip().capitalize()
        if priority not in PRIORITY_LEVELS:
            raise ValueError(f"priority must be one of {PRIORITY_LEVELS}, got '{priority}'")
        self.priority = priority

    def to_dict(self):
        data = super().to_dict()
        data["priority"] = self.priority
        return data

    def _detail_parts(self):
        return [f"Priority: {self.priority}"]

    def __repr__(self):
        return (f"PriorityTask(id={self.id}, description='{self.description}', "
                f"priority='{self.priority}', completed={self.completed}, tags={self.tags})")


# ใช้แปลง '_type' ใน JSON กลับเป็นคลาสที่ถูกต้อง
TASK_TYPES = {cls.TYPE_NAME: cls for cls in (Task, DueDateTask, PriorityTask)}


def task_from_dict(data):
    """
    สร้าง Task / DueDateTask / PriorityTask จาก dict ที่โหลดจาก JSON
    Raises: ValueError / TypeError / KeyError ถ้าข้อมูลไม่ถูกต้อง
    """
    fields = dict(data)
    type_name = fields.pop("_type", "Task")
    cls = TASK_TYPES.get(type_name)
    if cls is None:
        raise ValueError(f"unknown task type '{type_name}'")
    if not isinstance(fields.get("id"), int) or not isinstance(fields.get("description"), str):
        raise ValueError("task needs an integer 'id' and a string 'description'")
    return cls(**fields)
