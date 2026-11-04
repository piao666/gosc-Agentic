"""Actual installed httpx via MockTransport on HPC, never a network request."""
import json
import os
from pathlib import Path
import socket
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from hpc_runs import require_hpc
require_hpc()
import httpx
from extensions.masbench_reasoning.client import (ClientConfig,ContextBinding,ControlledClient,
    OllamaHTTPBackend,LivePermit,ClientFailure,JsonlAuditSink)


class HTTPMockContracts(unittest.TestCase):
    def setUp(self):
        self.original_connect = socket.socket.connect
        self.network_attempts = []
        def forbidden(*args,**kwargs):
            self.network_attempts.append(True)
            raise AssertionError("Real network forbidden")
        socket.socket.connect = forbidden
        self.requests=[]

    def tearDown(self):
        socket.socket.connect = self.original_connect
        self.assertEqual(self.network_attempts,[])

    def make_client(self, mode):
        cfg=ClientConfig("mock-model","a"*64,32768)
        def handler(request):
            self.requests.append(request)
            if request.method=="GET":
                if mode=="metadata_timeout":
                    raise httpx.ReadTimeout("synthetic",request=request)
                return httpx.Response(200,json={"models":[{"name":"mock-model","digest":"a"*64}]})
            if mode=="timeout":
                raise httpx.ReadTimeout("synthetic",request=request)
            if mode=="redirect":
                return httpx.Response(302,headers={"Location":"https://example.invalid/cloud"})
            return httpx.Response(200,json={"model":"mock-model","choices":[{"finish_reason":"stop","message":{"content":"<A>ok</A>"}}],
                                             "usage":None if mode=="missing_usage" else {"prompt_tokens":10,"completion_tokens":2,"total_tokens":12}})
        http=httpx.Client(transport=httpx.MockTransport(handler),trust_env=False,follow_redirects=False)
        self.addCleanup(http.close)
        self.assertFalse(http.trust_env)
        self.assertFalse(http.follow_redirects)
        permit=LivePermit("b"*64,"c"*64)
        backend=OllamaHTTPBackend(cfg,permit=permit,http_client=http)
        backend.is_live=False  # Explicitly identify this mock-only fixture in audit.
        return ControlledClient(cfg,backend,lambda _:10,ContextBinding("a"*64,32768,"mock-tokenizer","d"*64,True))

    def test_serialization_hash_and_local_endpoint(self):
        client=self.make_client("ok")
        self.assertEqual(client.generate([{"role":"system","content":"SYNTHETIC私有"}]),"<A>ok</A>")
        self.assertEqual(len(self.requests),2)
        self.assertEqual(str(self.requests[1].url),"http://127.0.0.1:11434/v1/chat/completions")
        self.assertFalse(json.loads(self.requests[1].content)["stream"])
        self.assertEqual(client.audit[0]["usage"]["total_tokens"],12)

    def test_no_redirect_following(self):
        client=self.make_client("redirect")
        with self.assertRaisesRegex(ClientFailure,"model_http_error_302"):
            client.generate([{"role":"system","content":"SYNTHETIC"}])
        self.assertEqual(len(self.requests),2)

    def test_real_httpx_timeout_class(self):
        client=self.make_client("timeout")
        with self.assertRaisesRegex(ClientFailure,"timeout"):
            client.generate([{"role":"system","content":"SYNTHETIC"}])
        self.assertEqual(client.calls,1)

    def test_metadata_timeout_is_not_a_generation(self):
        client=self.make_client("metadata_timeout")
        with self.assertRaisesRegex(ClientFailure,"timeout"):
            client.generate([{"role":"system","content":"SYNTHETIC"}])
        self.assertEqual(client.calls,0)

    def test_missing_usage_remains_missing(self):
        client=self.make_client("missing_usage")
        client.generate([{"role":"system","content":"SYNTHETIC"}])
        self.assertIsNone(client.audit[0]["usage"])
        self.assertTrue(client.audit[0]["usage_missing"])


if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(HTTPMockContracts)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    out=Path(os.environ["GOSC_OUTPUT_DIR"])
    (out/"httpx_mock_contract.json").write_text(json.dumps({"python":sys.executable,"httpx_version":httpx.__version__,
        "tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
        "transport":"httpx.MockTransport","actual_network_calls":0,"actual_model_calls":0},indent=2)+"\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
