"""Offline structure checks for the jurisprudentie-overzicht skill (no network)."""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FORBIDDEN = ["/users/"]
# ECLI's in the example, each fetched from data.rechtspraak.nl on 2026-09-23
# and checked against the claim made about it (see test-reports/jurisprudentie-overzicht.md).
VERIFIED_ECLIS = {
    "ECLI:NL:HR:2019:1734", "ECLI:NL:RBNHO:2020:2664", "ECLI:NL:RBMNE:2021:3076",
    "ECLI:NL:RBLIM:2025:13266", "ECLI:NL:RBAMS:2020:5427", "ECLI:NL:RBOVE:2021:1576",
    "ECLI:NL:GHSHE:2021:2156", "ECLI:NL:RBLIM:2019:3331", "ECLI:NL:RBOVE:2020:2309",
    "ECLI:NL:GHARL:2026:5624", "ECLI:NL:PHR:2023:914", "ECLI:NL:PHR:2024:545",
}
EXAMPLE = SKILL / "examples" / "voorbeeld-slapend-dienstverband.md"


def overview_part(text):
    return text[text.index("**Aan**"):text.index("# Zoekverantwoording")]


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

    def test_example_eclis_are_verified(self):
        text = EXAMPLE.read_text(encoding="utf-8")
        for ecli in re.findall(r"ECLI:[A-Z]{2}:[A-Z]+:\d{4}:[A-Z0-9]+", text):
            self.assertIn(ecli, VERIFIED_ECLIS)

    def test_example_structure(self):
        part = overview_part(EXAMPLE.read_text(encoding="utf-8"))
        own = "\n".join(l for l in part.splitlines() if not l.startswith(">"))
        self.assertNotIn(" — ", own)
        self.assertNotIn(" – ", own)
        self.assertFalse(re.search(r"^\s*[-*] ", own, re.M))
        sections = [int(n) for n in re.findall(r"^## (\d+)\.", part, re.M)]
        self.assertEqual(sections, list(range(1, len(sections) + 1)))
        nums = [int(n) for n in re.findall(r"^\*\*(\d+)\.\*\*", part, re.M)]
        self.assertEqual(nums, list(range(1, len(nums) + 1)))
        # every ruling paragraph (bold heading with ECLI) ends with an "Uitkomst:" line
        blocks = re.split(r"^\*\*\d+\.\*\* ", part, flags=re.M)
        for block in blocks:
            if re.match(r"\*\*[^*]*ECLI:", block):
                self.assertIn("Uitkomst:", block)


if __name__ == "__main__":
    unittest.main()
