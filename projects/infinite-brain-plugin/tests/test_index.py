import unittest

from infinite_brain.index import RepoIndex
from infinite_brain.retrieval import search

from helpers import make_repo


class RepoIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = make_repo()
        cls.index = RepoIndex(cls.tmp.name).build()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_indexes_only_frontmatter_nodes(self):
        ids = {n.id for n in self.index.all_nodes()}
        self.assertEqual(ids, {"node-alpha", "node-beta"})

    def test_skips_shim_directories(self):
        paths = [n.path for n in self.index.all_nodes()]
        self.assertFalse(any(p.startswith(".claude") for p in paths))

    def test_alias_lookup(self):
        node = self.index.get("alpha")
        self.assertIsNotNone(node)
        self.assertEqual(node.id, "node-alpha")

    def test_edges_parsed(self):
        node = self.index.get("node-alpha")
        self.assertEqual(node.edges[0]["relation"], "references")

    def test_namespaces_and_stats(self):
        self.assertEqual(self.index.namespaces(), [{"namespace": "demo", "node_count": 2}])
        stats = self.index.stats()
        self.assertEqual(stats["node_count"], 2)
        self.assertEqual(stats["by_type"], {"Knowledge": 1, "Skill": 1})

    def test_read_repo_file_refuses_escape(self):
        self.assertIsNone(self.index.read_repo_file("../outside.md"))
        self.assertIsNotNone(self.index.read_repo_file("knowledge/demo/a.md"))


class SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = make_repo()
        cls.index = RepoIndex(cls.tmp.name).build()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_ranked_results(self):
        results = search(self.index, "session startup doctrine")
        self.assertTrue(results)
        self.assertEqual(results[0]["id"], "node-alpha")
        self.assertNotIn("body", results[0])
        self.assertGreater(results[0]["score"], 0)

    def test_type_filter(self):
        results = search(self.index, "session", type="Skill")
        self.assertEqual([r["id"] for r in results], ["node-beta"])

    def test_lifecycle_filter(self):
        results = search(self.index, "session", lifecycle_state="canon")
        self.assertEqual([r["id"] for r in results], ["node-alpha"])

    def test_no_match(self):
        self.assertEqual(search(self.index, "zzz-no-such-token"), [])


if __name__ == "__main__":
    unittest.main()
