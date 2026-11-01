"""Local OpenAI chat-completions bridge for Hermes auxiliary.approval."""

import asyncio
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from smart_approval_loop.core.judges import Decision, Judge, judge_safely


class _Handler(BaseHTTPRequestHandler):
    server: "ApprovalHTTPServer"

    def do_POST(self) -> None:
        if self.path != "/chat/completions":
            self._reply(404, {"error": {"message": "not found"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_048_576:
                raise ValueError("invalid content length")
            payload = json.loads(self.rfile.read(length))
            messages = payload["messages"]
            if not isinstance(messages, list) or not messages:
                raise ValueError("messages must be a non-empty list")
            system = "\n".join(str(m["content"]) for m in messages if m.get("role") == "system")
            user = "\n".join(str(m["content"]) for m in messages if m.get("role") == "user")
            if not user:
                raise ValueError("messages must include a user message")
            event = {"source": "hermes", "event": "approval", "description": user,
                     "policy": system, "hermes": {"system_prompt": system, "user_prompt": user}}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._reply(400, {"error": {"message": "invalid chat completion request"}})
            return
        judgment = asyncio.run(judge_safely(self.server.judge, event, self.server.timeout))
        body = {"id": "chatcmpl-" + uuid.uuid4().hex, "object": "chat.completion",
                "created": 0, "model": payload.get("model", "smart-approval-loop"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": judgment.decision.value},
                             "finish_reason": "stop"}]}
        self._reply(200, body)

    def _reply(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        return


class ApprovalHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], judge: Judge, timeout: float):
        super().__init__(address, _Handler)
        self.judge = judge
        self.timeout = timeout


def create_server(host: str, port: int, judge: Judge, timeout: float = 5.0) -> ApprovalHTTPServer:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    return ApprovalHTTPServer((host, port), judge, timeout)


def main() -> None:
    """Run a local bridge using the configured OpenAI-compatible judge endpoint."""
    from urllib.request import Request, urlopen
    from smart_approval_loop.core.judges import ChatCompletionsJudge

    judge_url = os.environ.get("SMART_APPROVAL_LOOP_JUDGE_URL")
    if not judge_url:
        raise SystemExit("Set SMART_APPROVAL_LOOP_JUDGE_URL to an OpenAI-compatible /chat/completions URL")
    model = os.environ.get("SMART_APPROVAL_LOOP_JUDGE_MODEL", "")
    token = os.environ.get("SMART_APPROVAL_LOOP_JUDGE_API_KEY", "")
    timeout = float(os.environ.get("SMART_APPROVAL_LOOP_TIMEOUT", "5"))

    async def transport(messages: list[dict[str, str]]) -> dict[str, Any]:
        request_body = {"model": model, "messages": messages, "temperature": 0, "max_tokens": 16}
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(judge_url, data=json.dumps(request_body).encode(), headers=headers)
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())

    judge = ChatCompletionsJudge(transport)
    host = os.environ.get("SMART_APPROVAL_LOOP_HOST", "127.0.0.1")
    port = int(os.environ.get("SMART_APPROVAL_LOOP_PORT", "8765"))
    server = create_server(host, port, judge, timeout)
    print(f"Hermes approval bridge listening at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
