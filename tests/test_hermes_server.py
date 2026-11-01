import json
import threading
import urllib.error
import urllib.request

from smart_approval_loop.adapters.hermes.server import create_server


class FixedJudge:
    def __init__(self, decision):
        self.decision = decision
        self.event = None

    async def judge(self, event):
        self.event = event
        from smart_approval_loop.core.judges import Judgment
        return Judgment(self.decision, "test")


def test_chat_completions_returns_single_word_for_each_verdict():
    from smart_approval_loop.core.judges import Decision

    for decision in Decision:
        judge = FixedJudge(decision)
        server = create_server("127.0.0.1", 0, judge)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = json.dumps({"model": "local", "messages": [
                {"role": "system", "content": "policy"},
                {"role": "user", "content": "run safe command"},
            ]}).encode()
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/chat/completions",
                data=body, headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request) as response:
                result = json.load(response)
            assert result["choices"][0]["message"]["content"] == decision.value
            assert result["model"] == "local"
            assert judge.event["hermes"]["system_prompt"] == "policy"
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def test_invalid_request_is_rejected():
    server = create_server("127.0.0.1", 0, FixedJudge(None))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/chat/completions",
            data=b"{}", headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("invalid request accepted")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
