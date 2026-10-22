# src/data_persistence.py
"""
Data Layer: บันทึกและโหลด Task objects จากไฟล์ JSON
แยกงาน File I/O ออกจาก Business Logic (Separation of Concerns)
"""

import json
import os

from .task import task_from_dict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DataPersistence:
    """โหลด/บันทึกรายการงานในไฟล์ JSON"""

    def __init__(self, data_file=os.path.join("data", "tasks.json")):
        # path สัมพัทธ์จะนับจากโฟลเดอร์โปรเจกต์ (รันจากโฟลเดอร์ไหนก็ได้)
        self.data_file = data_file
        self._path = data_file if os.path.isabs(data_file) else os.path.join(PROJECT_DIR, data_file)

    def get_file_path(self):
        return self._path

    def load_tasks(self):
        """โหลดงานจาก JSON ถ้าไฟล์ไม่มี/ว่าง/เสีย จะเริ่มด้วยรายการว่าง และข้ามรายการที่ข้อมูลผิด"""
        if not os.path.exists(self._path):
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            raw_tasks = json.loads(content) if content else []
        except json.JSONDecodeError:
            print("Warning: ไฟล์ tasks.json รูปแบบไม่ถูกต้อง กำลังเริ่มด้วยรายการงานว่าง")
            return []
        except OSError as e:
            print(f"Warning: อ่านไฟล์ {self._path} ไม่ได้ ({e}) กำลังเริ่มด้วยรายการงานว่าง")
            return []

        if not isinstance(raw_tasks, list):
            print("Warning: tasks.json ไม่ได้เก็บข้อมูลเป็นลิสต์ กำลังเริ่มด้วยรายการงานว่าง")
            return []

        tasks, seen_ids = [], set()
        for item in raw_tasks:
            try:
                if not isinstance(item, dict):
                    raise ValueError("entry is not an object")
                task = task_from_dict(item)
                if task.id in seen_ids:
                    raise ValueError(f"duplicate id {task.id}")
            except (ValueError, TypeError, KeyError) as e:
                print(f"Warning: ข้ามรายการงานที่ไม่ถูกต้อง ({e}): {item}")
                continue
            seen_ids.add(task.id)
            tasks.append(task)
        return tasks

    def save_tasks(self, tasks):
        """
        บันทึกงานทั้งหมด (เรียก to_dict() ของแต่ละ object ตามหลัก Polymorphism)
        เขียนไฟล์ชั่วคราวก่อนแล้วค่อยแทนที่ เพื่อไม่ให้ tasks.json เสียถ้าโปรแกรมหยุดกลางคัน
        คืน True ถ้าบันทึกสำเร็จ
        """
        temp_path = self._path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump([task.to_dict() for task in tasks], f, indent=4, ensure_ascii=False)
            os.replace(temp_path, self._path)
            return True
        except OSError as e:
            print(f"ข้อผิดพลาด: บันทึกไฟล์ไม่สำเร็จ ({e})")
            return False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
