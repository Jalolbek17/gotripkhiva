import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from urllib.request import Request, urlopen

HOST = ""
PORT = 8000
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


class TravelHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if urlparse(self.path).path != "/api/telegram":
            self.send_error(404)
            return

        load_env_file()
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "put_new_bot_token_here":
            self.send_json(503, {"ok": False, "error": "TELEGRAM_BOT_TOKEN is not configured"})
            return
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", CHAT_ID).strip()
        if not chat_id:
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
                data=json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8"),
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

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    load_env_file()
    server = ThreadingHTTPServer((HOST, PORT), TravelHandler)
    print(f"Travel site: http://localhost:{PORT}/arthouseaccomadation.html")
    print("Telegram endpoint: /api/telegram")
    server.serve_forever()
