"""Offline structure checks for the bronvermelding skill (no network)."""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FORBIDDEN = ["/users/"]
# Every ECLI used in this skill was fetched from data.rechtspraak.nl or publications.europa.eu
# on 2026-09-23 and checked against what the skill says about it.
VERIFIED_ECLIS = {
    "ECLI:NL:HR:1981:AG4158", "ECLI:NL:HR:2019:1734", "ECLI:NL:GHSHE:2021:2156",
    "ECLI:NL:RBNHO:2020:2664", "ECLI:NL:PHR:2023:914",
    "ECLI:EU:C:2014:317", "ECLI:EU:C:2015:357",
}
# Examples that the local Leidraad summaries reuse from the Leidraad itself; they must not appear here.
LEIDRAAD_EXAMPLES = ["Botman", "Van Opijnen", "Hugenholtz", "ECLI:NL:HR:2016:162", "Lindenbaum",
                     "Baladin", "34442", "Tourancheau", "Van Verseveld", "Ancery"]


class TestStructuur(unittest.TestCase):
    def all_md(self):
        return {p: p.read_text(encoding="utf-8") for p in SKILL.rglob("*.md")}

    def test_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), SKILL.name)

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"`((?:references|templates|examples)/[^`]+)`", text):
            self.assertTrue((SKILL / ref).exists(), ref)

    def test_openai_yaml_implicit(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", text)
        self.assertIn("allow_implicit_invocation: true", text)

    def test_no_forbidden_terms(self):
        for path, text in self.all_md().items():
            for term in FORBIDDEN:
                self.assertNotIn(term, text.lower(), f"{term} in {path.name}")

    def test_eclis_verified(self):
        for path, text in self.all_md().items():
            for ecli in re.findall(r"ECLI:[A-Z]{2}:[A-Z]+:\d{4}:[A-Z0-9]+", text):
                self.assertIn(ecli, VERIFIED_ECLIS, f"{ecli} in {path.name}")

    def test_no_leidraad_examples(self):
        for path, text in self.all_md().items():
            for name in LEIDRAAD_EXAMPLES:
                self.assertNotIn(name, text, f"{name} in {path.name}")


if __name__ == "__main__":
    unittest.main()
