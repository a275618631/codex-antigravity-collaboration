import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "bridge_server.py"


def rpc(process, request):
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline())


class BridgeServerTests(unittest.TestCase):
    def test_two_clients_can_exchange_messages(self):
        with tempfile.TemporaryDirectory() as mailbox:
            env = os.environ.copy()
            env["CODEX_ANTIGRAVITY_BRIDGE_HOME"] = mailbox

            codex = subprocess.Popen(
                ["python3", str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env={**env, "CODEX_ANTIGRAVITY_BRIDGE_AGENT": "codex"},
            )
            antigravity = subprocess.Popen(
                ["python3", str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env={**env, "CODEX_ANTIGRAVITY_BRIDGE_AGENT": "antigravity"},
            )
            try:
                self.assertEqual(rpc(codex, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})["result"]["serverInfo"]["name"], "codex-antigravity-bridge")
                self.assertEqual(len(rpc(antigravity, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]), 4)

                sent = rpc(codex, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "bridge_send", "arguments": {"target": "antigravity", "subject": "smoke", "message": "hello from codex"}}})
                self.assertFalse(sent["result"].get("isError", False))

                received = rpc(antigravity, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "bridge_receive", "arguments": {}}})
                payload = json.loads(received["result"]["content"][0]["text"])
                self.assertEqual(payload["messages"][0]["sender"], "codex")
                self.assertEqual(payload["messages"][0]["message"], "hello from codex")

                rpc(antigravity, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "bridge_send", "arguments": {"target": "codex", "message": "hello from antigravity"}}})
                reply = rpc(codex, {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "bridge_receive", "arguments": {}}})
                reply_payload = json.loads(reply["result"]["content"][0]["text"])
                self.assertEqual(reply_payload["messages"][0]["sender"], "antigravity")
            finally:
                for process in (codex, antigravity):
                    process.terminate()
                    process.wait(timeout=5)
                    process.stdin.close()
                    process.stdout.close()
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()
