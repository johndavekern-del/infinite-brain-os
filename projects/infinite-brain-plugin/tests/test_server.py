import json
import threading
import unittest
import urllib.request
import urllib.error

from infinite_brain.index import RepoIndex
from infinite_brain.server import BrainHTTPServer

from helpers import make_repo


def get_json(port, path):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}") as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = make_repo()
        index = RepoIndex(cls.tmp.name).build()
        cls.server = BrainHTTPServer(("127.0.0.1", 0), index)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def test_health(self):
        status, data = get_json(self.port, "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["node_count"], 2)

    def test_manifest(self):
        status, data = get_json(self.port, "/plugin.json")
        self.assertEqual(status, 200)
        self.assertEqual(data["name"], "infinite-brain")
        self.assertEqual(data["mutability"], "read-only")
        self.assertTrue(any(e["path"] == "/v1/search" for e in data["endpoints"]))

    def test_openapi(self):
        status, data = get_json(self.port, "/openapi.json")
        self.assertEqual(status, 200)
        self.assertIn("/v1/search", data["paths"])

    def test_search_endpoint(self):
        status, data = get_json(self.port, "/v1/search?q=session+startup")
        self.assertEqual(status, 200)
        self.assertEqual(data["results"][0]["id"], "node-alpha")

    def test_search_requires_q(self):
        status, data = get_json(self.port, "/v1/search")
        self.assertEqual(status, 400)

    def test_get_node_and_404(self):
        status, data = get_json(self.port, "/v1/nodes/alpha")
        self.assertEqual(status, 200)
        self.assertIn("Read this card first", data["body"])
        status, _ = get_json(self.port, "/v1/nodes/nope")
        self.assertEqual(status, 404)

    def test_namespaces_and_load_order(self):
        status, data = get_json(self.port, "/v1/namespaces")
        self.assertEqual(status, 200)
        status, data = get_json(self.port, "/v1/namespaces/demo/load_order")
        self.assertEqual(status, 200)
        self.assertIn("canon first", data["content"])
        status, _ = get_json(self.port, "/v1/namespaces/missing/load_order")
        self.assertEqual(status, 404)
        status, _ = get_json(self.port, "/v1/namespaces/bad../name/load_order")
        self.assertEqual(status, 400)

    def test_unknown_path(self):
        status, _ = get_json(self.port, "/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
