# tests/test_api_client.py
# Unit tests for APIClient. The HTTP layer is mocked, so the tests run offline and never call the real API.
import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

import requests

from src.api_client import APIClient


def make_response(json_data=None, status=200, json_error=False):
    """Builds a fake requests.Response."""
    response = MagicMock()
    response.status_code = status
    if status >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status} Error", response=response)
    if json_error:
        response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
    else:
        response.json.return_value = json_data
    return response


class TestAPIClient(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()
        patcher = patch.object(self.client.session, "get")
        self.mock_get = patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, method, *args):
        """Calls a client method without printing its log lines."""
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = method(*args)
        return result, output.getvalue()

    def test_fetch_single_todo_success(self):
        todo = {"userId": 1, "id": 1, "title": "delectus aut autem", "completed": False}
        self.mock_get.return_value = make_response(todo)
        result, _ = self.call(self.client.fetch_single_todo, 1)
        self.assertEqual(result, todo)
        self.assertEqual(self.mock_get.call_args.args[0], "https://jsonplaceholder.typicode.com/todos/1")

    def test_fetch_all_posts_returns_list(self):
        posts = [{"id": i, "userId": 1, "title": f"t{i}", "body": "b"} for i in range(1, 4)]
        self.mock_get.return_value = make_response(posts)
        result, _ = self.call(self.client.fetch_all_posts)
        self.assertEqual(len(result), 3)

    def test_fetch_user_todos_uses_query_params(self):
        self.mock_get.return_value = make_response([{"id": 1, "userId": 2, "title": "x", "completed": True}])
        self.call(self.client.fetch_user_todos, 2)
        self.assertEqual(self.mock_get.call_args.args[0], "https://jsonplaceholder.typicode.com/todos")
        self.assertEqual(self.mock_get.call_args.kwargs["params"], {"userId": 2})

    def test_404_returns_none(self):
        self.mock_get.return_value = make_response(status=404)
        result, output = self.call(self.client.fetch_single_todo, 9999)
        self.assertIsNone(result)
        self.assertIn("404", output)

    def test_server_error_returns_none(self):
        self.mock_get.return_value = make_response(status=500)
        result, output = self.call(self.client.fetch_all_posts)
        self.assertIsNone(result)
        self.assertIn("500", output)

    def test_connection_error_returns_none(self):
        self.mock_get.side_effect = requests.exceptions.ConnectionError("no network")
        result, output = self.call(self.client.fetch_all_posts)
        self.assertIsNone(result)
        self.assertIn("Connection Error", output)

    def test_timeout_returns_none(self):
        self.mock_get.side_effect = requests.exceptions.Timeout()
        result, output = self.call(self.client.fetch_user_todos, 1)
        self.assertIsNone(result)
        self.assertIn("Timeout", output)

    def test_invalid_json_returns_none(self):
        self.mock_get.return_value = make_response(json_error=True)
        result, output = self.call(self.client.fetch_single_todo, 1)
        self.assertIsNone(result)
        self.assertIn("JSON Decode Error", output)

    def test_unexpected_data_type_returns_none(self):
        # /posts should be a list; a dict means the API answered something unexpected
        self.mock_get.return_value = make_response({"error": "unexpected"})
        result, output = self.call(self.client.fetch_all_posts)
        self.assertIsNone(result)
        self.assertIn("ไม่ถูกต้อง", output)

    def test_every_request_has_a_timeout(self):
        self.mock_get.return_value = make_response([])
        self.call(self.client.fetch_all_posts)
        self.assertEqual(self.mock_get.call_args.kwargs["timeout"], 10)


if __name__ == "__main__":
    unittest.main()
