# Week 10 Class Activity 3: Interacting with Web APIs - Fetching and Processing JSON Data

An interactive CLI that calls the [JSONPlaceholder](https://jsonplaceholder.typicode.com) REST API with
`requests`, turns the JSON responses into Python dicts/lists, and displays/summarises them.
Network and data errors are handled without crashing.

## Results (screenshots)

### 1. Fetch a Single TODO Item
![Fetch single TODO](screenshots/1_fetch_single_todo.png)

### 2. Fetch All Posts
![Fetch all posts](screenshots/2_fetch_all_posts.png)

### 3. Fetch TODOs by User ID
![Fetch TODOs by user](screenshots/3_fetch_user_todos.png)

## How to Run

```bash
cd Week10/my-api-fetcher
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py                    # interactive menu (needs internet)
python -m unittest discover -v    # 10 unit tests (offline, the API is mocked)
```

## Menu

| Option | Endpoint | Output |
|--------|----------|--------|
| 1. Fetch Single TODO | `GET /todos/{id}` | ID, user, title and status of one TODO |
| 2. Fetch All Posts | `GET /posts` | first 5 posts (title + body preview), total count, posts per user |
| 3. Fetch User TODOs | `GET /todos?userId={id}` | every TODO of that user + completed / pending summary (%) |
| 4. Exit | | |

## Project Structure

```
my-api-fetcher/
├── src/
│   ├── __init__.py
│   └── api_client.py       # APIClient: HTTP GET, JSON parsing, error handling
├── tests/
│   └── test_api_client.py  # unit tests with unittest.mock (no real network calls)
├── screenshots/
├── main.py                 # CLI menu: input validation and display
├── requirements.txt        # requests
└── README.md
```

## Error Handling

| Problem | Result |
|---------|--------|
| Input is not a number / not positive | `❌` message, back to the menu (no request is sent) |
| `404 Not Found` (e.g. TODO 9999) | `[ERROR] HTTP 404` + "ไม่พบข้อมูล" |
| Other 4xx / 5xx | `[ERROR] HTTP Error (code)` |
| No internet / wrong domain | `[ERROR] Connection Error` |
| Server too slow | `[ERROR] Timeout` (every request has a 10 s timeout) |
| Response is not JSON | `[ERROR] JSON Decode Error` |
| JSON has the wrong shape (e.g. dict instead of list) | rejected before the CLI uses it |
| User with no TODOs (e.g. 999) | "ไม่พบรายการงาน TODO" |
| `Ctrl+C` / `Ctrl+D` | exits cleanly |

## Notes on the implementation

* `requests.Session` reuses one connection for all calls and sends an `Accept: application/json` header.
* Query parameters are passed with `params={"userId": 1}` so `requests` builds and encodes `?userId=1`.
* `requests.exceptions.JSONDecodeError` is caught **before** `RequestException`, because it is a subclass of it.
