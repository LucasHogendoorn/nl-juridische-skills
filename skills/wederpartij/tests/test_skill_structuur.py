"""Offline structure checks for the wederpartij skill (no network)."""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FORBIDDEN = ["/users/"]
EXAMPLE = SKILL / "examples" / "voorbeeld-huurder-zelf-vervangen.md"
FIELDS = ["**Sterkte**:", "**Vindplaats**:", "**Objectie**:", "**Waarom het werkt**:", "**Nodig om te weerleggen**:"]


class TestStructuur(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), SKILL.name)

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"`((?:references|templates|examples)/[^`]+)`", text):
            self.assertTrue((SKILL / ref).exists(), ref)

    def test_openai_yaml(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", text)
        self.assertIn("allow_implicit_invocation: false", text)

    def test_no_forbidden_terms(self):
        for path in SKILL.rglob("*.md"):
            low = path.read_text(encoding="utf-8").lower()
            for term in FORBIDDEN:
                self.assertNotIn(term, low, f"{term} in {path.name}")

    def test_example_objections_complete(self):
        text = EXAMPLE.read_text(encoding="utf-8")
        review = text[text.index("# Tegenlezing"):]
        blocks = re.split(r"^## Bezwaar \d+: ", review, flags=re.M)[1:]
        self.assertGreaterEqual(len(blocks), 1)
        self.assertLessEqual(len(blocks), 12)
        counts = {"kritiek": 0, "wezenlijk": 0, "beperkt": 0}
        for block in blocks:
            for field in FIELDS:
                self.assertIn(field, block)
            level = re.search(r"\*\*Sterkte\*\*: (\w+)", block).group(1)
            self.assertIn(level, counts)
            counts[level] += 1
        status = re.search(r"\*\*Status\*\*: ZIE BEZWAREN \((\d+): (\d+) kritiek, (\d+) wezenlijk, (\d+) beperkt\)", review)
        self.assertIsNotNone(status)
        self.assertEqual(int(status.group(1)), len(blocks))
        self.assertEqual([int(status.group(i)) for i in (2, 3, 4)],
                         [counts["kritiek"], counts["wezenlijk"], counts["beperkt"]])


if __name__ == "__main__":
    unittest.main()
