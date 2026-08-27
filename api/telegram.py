import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen


CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            self.send_json(503, {"ok": False, "error": "TELEGRAM_BOT_TOKEN is not configured"})
            return
        if not CHAT_ID:
            self.send_json(503, {"ok": False, "error": "TELEGRAM_CHAT_ID is not configured"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(payload.get("message", "")).strip()
            if not message:
                self.send_json(400, {"ok": False, "error": "Message is empty"})
                return

            telegram_request = Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=json.dumps({"chat_id": CHAT_ID, "text": message}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(telegram_request, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.send_json(200 if result.get("ok") else 502, result)
        except Exception as error:
            detail = getattr(error, "read", lambda: b"")()
            try:
                detail = json.loads(detail.decode("utf-8"))
            except Exception:
                detail = str(error)
            self.send_json(502, {"ok": False, "error": detail})

    def do_OPTIONS(self):
        self.send_json(204, {})

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)