import unittest

from infinite_brain.frontmatter import loads, parse_frontmatter


SAMPLE = """---
id: "sample-node"
aliases: ["sample-node", "sample"]
type: "Knowledge"
namespace: "demo"
lifecycle_state: "research"
summary: "A summary with a colon: still one string."
confidence: 0.9
retrieval_class: "domain"
export_class: "internal"
party_slugs: []
client_slug: null
verified: true
edges:
  - target: "[[core-doctrine]]"
    relation: "derived_from"
    confidence: 0.95
  - target: "[[other-node]]"
    relation: "references"
plain_list:
  - "alpha"
  - "beta"
created: "2026-10-12"
---

# Body title

Body text here.
"""


class LoadsTest(unittest.TestCase):
    def test_scalars(self):
        data = loads(SAMPLE.split("---")[1])
        self.assertEqual(data["id"], "sample-node")
        self.assertEqual(data["confidence"], 0.9)
        self.assertIsNone(data["client_slug"])
        self.assertTrue(data["verified"])

    def test_summary_with_colon(self):
        data = loads(SAMPLE.split("---")[1])
        self.assertEqual(data["summary"], "A summary with a colon: still one string.")

    def test_inline_and_empty_lists(self):
        data = loads(SAMPLE.split("---")[1])
        self.assertEqual(data["aliases"], ["sample-node", "sample"])
        self.assertEqual(data["party_slugs"], [])

    def test_block_sequence_of_mappings(self):
        data = loads(SAMPLE.split("---")[1])
        self.assertEqual(len(data["edges"]), 2)
        self.assertEqual(data["edges"][0]["target"], "[[core-doctrine]]")
        self.assertEqual(data["edges"][0]["relation"], "derived_from")
        self.assertEqual(data["edges"][0]["confidence"], 0.95)
        self.assertEqual(data["edges"][1]["target"], "[[other-node]]")

    def test_block_sequence_of_scalars(self):
        data = loads(SAMPLE.split("---")[1])
        self.assertEqual(data["plain_list"], ["alpha", "beta"])


class ParseFrontmatterTest(unittest.TestCase):
    def test_split_meta_and_body(self):
        meta, body = parse_frontmatter(SAMPLE)
        self.assertEqual(meta["id"], "sample-node")
        self.assertIn("# Body title", body)

    def test_no_frontmatter(self):
        meta, body = parse_frontmatter("# Just markdown\n")
        self.assertEqual(meta, {})
        self.assertIn("Just markdown", body)


if __name__ == "__main__":
    unittest.main()
