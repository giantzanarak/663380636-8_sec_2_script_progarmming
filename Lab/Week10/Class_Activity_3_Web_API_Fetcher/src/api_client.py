"""
src/api_client.py
โมดูลสำหรับติดต่อสื่อสารกับ Web API (JSONPlaceholder)
"""

from typing import Any, Dict, List, Optional

import requests


class APIClient:
    """
    ตัวกลางสำหรับส่ง HTTP GET Request ไปยัง REST API และแปลงผลลัพธ์ JSON
    เป็น Python Data Structure (dict / list) พร้อมจัดการข้อผิดพลาดทุกกรณี
    """

    DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10) -> None:
        """
        :param base_url: URL ฐานของ API (ไม่ระบุ = JSONPlaceholder)
        :param timeout: เวลารอการตอบกลับสูงสุด (วินาที) ป้องกันโปรแกรมค้าง
        """
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        # ใช้ Session เดียวตลอดการทำงาน: reuse การเชื่อมต่อ ทำให้เรียกซ้ำได้เร็วขึ้น
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "my-api-fetcher/1.0"})

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        ส่ง GET Request ไปที่ endpoint แล้วคืนข้อมูล JSON ที่แปลงแล้ว หรือ None ถ้าเกิดข้อผิดพลาด

        :param endpoint: พาธปลายทาง เช่น '/todos/1' หรือ '/posts'
        :param params: Query Parameters เช่น {"userId": 1} -> ?userId=1 (requests ช่วย encode ให้)
        """
        url = f"{self.base_url}{endpoint}"
        print(f"[INFO] กำลังส่งคำขอ (GET) ไปที่: {url}" + (f" พร้อม params={params}" if params else ""))

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            # 4xx / 5xx -> HTTPError
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            status = err.response.status_code if err.response is not None else "?"
            if status == 404:
                print(f"[ERROR] HTTP 404: ไม่พบข้อมูลที่ {url}")
            else:
                print(f"[ERROR] HTTP Error ({status}): {err}")
        except requests.exceptions.ConnectionError:
            print("[ERROR] Connection Error: ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ (ตรวจสอบอินเทอร์เน็ต)")
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout: เซิร์ฟเวอร์ไม่ตอบกลับภายใน {self.timeout} วินาที")
        except requests.exceptions.JSONDecodeError:
            # ต้องอยู่ก่อน RequestException เพราะเป็น subclass ของมัน
            print("[ERROR] JSON Decode Error: ข้อมูลที่ได้รับไม่ใช่ JSON ที่ถูกต้อง")
        except requests.exceptions.RequestException as err:
            print(f"[ERROR] Request Exception: {err}")
        return None

    @staticmethod
    def _expect(data: Any, expected_type: type, what: str) -> Optional[Any]:
        """ตรวจว่าข้อมูลที่ได้เป็นชนิดที่คาดไว้ (dict / list) ก่อนส่งต่อให้โปรแกรมใช้"""
        if data is None:
            return None
        if not isinstance(data, expected_type):
            print(f"[ERROR] รูปแบบข้อมูล {what} ไม่ถูกต้อง: คาดว่าเป็น {expected_type.__name__} "
                  f"แต่ได้ {type(data).__name__}")
            return None
        return data

    def fetch_single_todo(self, todo_id: int) -> Optional[Dict[str, Any]]:
        """GET /todos/{todo_id} -> dict ของ TODO หนึ่งรายการ"""
        return self._expect(self._make_request(f"/todos/{todo_id}"), dict, "TODO")

    def fetch_all_posts(self) -> Optional[List[Dict[str, Any]]]:
        """GET /posts -> list ของโพสต์ทั้งหมด"""
        return self._expect(self._make_request("/posts"), list, "Posts")

    def fetch_user_todos(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """GET /todos?userId={user_id} -> list ของ TODO ของผู้ใช้คนนั้น"""
        return self._expect(self._make_request("/todos", params={"userId": user_id}), list, "User TODOs")
