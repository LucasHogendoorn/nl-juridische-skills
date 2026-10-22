"""Offline structure checks for the memo-schrijven skill (no network)."""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FORBIDDEN = ["/users/"]


def memo_part(text):
    """Return the memo itself: from the metadata block up to the decisions log."""
    start = text.index("**Aan**")
    end = text.index("# Beslissingenlog")
    return text[start:end]


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
        self.assertIn("short_description:", text)
        self.assertIn("allow_implicit_invocation: false", text)

    def test_no_forbidden_terms(self):
        for path in SKILL.rglob("*.md"):
            low = path.read_text(encoding="utf-8").lower()
            for term in FORBIDDEN:
                self.assertNotIn(term, low, f"{term} in {path.name}")

    def test_example_follows_own_style_rules(self):
        text = (SKILL / "examples" / "voorbeeld-huur-cv-ketel.md").read_text(encoding="utf-8")
        memo = memo_part(text)
        # no dashes as punctuation, no bullets, no footnotes
        self.assertNotIn(" — ", memo)
        self.assertNotIn(" – ", memo)
        self.assertFalse(re.search(r"^\s*[-*] ", memo, re.M))
        self.assertFalse(re.search(r"\[\^\d+\]", memo))
        # exactly five level-2 sections, no level-3
        self.assertEqual(len(re.findall(r"^## ", memo, re.M)), 5)
        self.assertFalse(re.search(r"^### ", memo, re.M))
        # consecutive paragraph numbers
        nums = [int(n) for n in re.findall(r"^\*\*(\d+)\.\*\*", memo, re.M)]
        self.assertEqual(nums, list(range(1, len(nums) + 1)))
        for banned in ["hoewel", "ten overvloede", "voor de volledigheid", "a.w.", "o.c.", "e.v."]:
            self.assertNotIn(banned, memo.lower())


if __name__ == "__main__":
    unittest.main()
