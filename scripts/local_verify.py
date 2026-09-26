import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

# Force UTF-8 stdout
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "synthetic" / "src"))

from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.bootstrap.settings import get_settings

settings = get_settings()
adapter = SyntheticIdentityAdapter(secret_key=settings.IDENTITY_SECRET_KEY, environment="local")

# Student identity
student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
student_token = adapter.mint_token(student_id)
student_headers = {
    "Authorization": f"Bearer {student_token}",
    "Content-Type": "application/json",
}

# Admin identity (Knowledge Admin)
admin_id = "61a945d3-8c1d-7d63-b2fa-4274128d269a"
admin_token = adapter.mint_token(admin_id)
admin_headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json",
}

def request_json(url, method='GET', data=None, headers=None):
    hdrs = dict(headers or {})
    req = urllib.request.Request(url, method=method, headers=hdrs)
    if data:
        req.data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            sample = body[:100].replace('\n', ' ')
            print(f"[{method}] {url} -> {resp.status} OK | Length: {len(body)} | Sample: {sample}")
            return resp.status, body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')[:200]
        print(f"[{method}] {url} -> HTTPError {e.code}: {err_body}")
        return e.code, None
    except Exception as e:
        print(f"[{method}] {url} -> Exception: {e}")
        return None, None

def main():
    print("=== 1. TESTING BACKEND FASTAPI ENDPOINTS ===")
    endpoints = [
        ("GET", "http://127.0.0.1:8000/health/live", None, {}),
        ("GET", "http://127.0.0.1:8000/health/ready", None, {}),
        ("GET", "http://127.0.0.1:8000/v1/rooms", None, student_headers),
        ("GET", "http://127.0.0.1:8000/v1/tickets", None, student_headers),
        ("GET", "http://127.0.0.1:8000/v1/knowledge/sources", None, admin_headers),
        ("GET", "http://127.0.0.1:8000/v1/privacy/notice", None, student_headers),
        ("GET", "http://127.0.0.1:8000/v1/students/me/schedule?from=2026-09-01T00:00:00Z&to=2026-09-30T23:59:59Z", None, student_headers),
        (
            "POST",
            "http://127.0.0.1:8000/v1/tickets/preview",
            {
                "category": "ACADEMIC_POLICY",
                "priority": "NORMAL",
                "subject": "Xin cấp bảng điểm tạm thời",
                "description": "Cần bảng điểm để nộp học bổng",
                "queue_key": "HUCE_GENERAL",
            },
            student_headers,
        ),
    ]

    all_passed = True
    for method, url, data, headers in endpoints:
        status, body = request_json(url, method, data, headers)
        if status not in (200, 201):
            all_passed = False

    # Test conversation creation & SSE stream
    print("\n--- Testing Conversation Creation & SSE Streaming ---")
    conv_status, conv_body = request_json(
        "http://127.0.0.1:8000/v1/conversations",
        "POST",
        {},
        student_headers,
    )
    if conv_status == 201 and conv_body:
        conv_id = json.loads(conv_body)["id"]
        print(f"Created conversation: {conv_id}")

        stream_status, stream_body = request_json(
            f"http://127.0.0.1:8000/v1/conversations/{conv_id}/messages:stream",
            "POST",
            {"content": "Học phí kỳ 1 năm 2026 đóng như thế nào?"},
            student_headers,
        )
        if stream_status == 200 and stream_body:
            has_started = "event: message.started" in stream_body
            has_delta = "event: message.delta" in stream_body
            has_completed = "event: message.completed" in stream_body
            print(f"SSE events verified: started={has_started}, delta={has_delta}, completed={has_completed}")
            if not (has_started and has_delta and has_completed):
                all_passed = False
        else:
            all_passed = False
    else:
        all_passed = False

    print("\n=== 2. TESTING FRONTEND WEB APP (PORT 3000) ===")
    frontend_pages = [
        "http://localhost:3000/",
        "http://localhost:3000/chat",
        "http://localhost:3000/schedule",
        "http://localhost:3000/tickets",
        "http://localhost:3000/rooms",
        "http://localhost:3000/staff",
        "http://localhost:3000/knowledge",
        "http://localhost:3000/privacy",
    ]
    for url in frontend_pages:
        status, _ = request_json(url, "GET")
        if status != 200:
            all_passed = False

    if all_passed:
        print("\n==============================================")
        print(">>> ALL LOCAL ENDPOINTS & PAGES VERIFIED (PASS) <<<")
        print("==============================================")
        sys.exit(0)
    else:
        print("\n>>> SOME CHECKS FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
