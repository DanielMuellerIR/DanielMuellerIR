"""Regressionstests für die Linkparität der beiden Profil-READMEs."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_readme_links import REPO_ROOT, github_links, main


FIRST = "https://github.com/example/first"
SECOND = "https://github.com/example/second"


class ReadmeLinksTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.english = Path(self.directory.name) / "en.md"
        self.german = Path(self.directory.name) / "de.md"

    def compare(self, english, german):
        self.english.write_text(english, encoding="utf-8")
        self.german.write_text(german, encoding="utf-8")
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = main([str(self.english), str(self.german)])
        return result, output.getvalue(), errors.getvalue()

    def test_actual_readmes_match(self):
        result, output, _ = self.compare(
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "README.de.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(result, 0)
        self.assertIn("20 GitHub-Links", output)

    def test_commented_project_in_actual_readme_fails(self):
        english = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        german = (REPO_ROOT / "README.de.md").read_text(encoding="utf-8")
        entry = next(line for line in german.splitlines() if "**[fastra]" in line)
        result, _, _ = self.compare(english, german.replace(entry, f"<!-- {entry} -->"))
        self.assertEqual(result, 1)

    def test_different_titled_links_in_actual_readmes_fail(self):
        english = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        german = (REPO_ROOT / "README.de.md").read_text(encoding="utf-8")
        result, _, _ = self.compare(
            english + f'\n[Extra]({FIRST} "Extra")\n',
            german + f'\n[Extra]({SECOND} "Extra")\n',
        )
        self.assertEqual(result, 1)

    def test_reflowed_actual_readme_matches(self):
        english = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        german = (REPO_ROOT / "README.de.md").read_text(encoding="utf-8")
        reflowed = german.replace("Die\nmeisten Projekte", "Die meisten Projekte")
        self.assertNotEqual(german, reflowed)
        result, _, _ = self.compare(english, reflowed)
        self.assertEqual(result, 0)

    def test_markdown_link_forms_match(self):
        variants = [
            f'[Project]({FIRST} "Title")',
            f"[Project](<{FIRST}> 'Title')",
            f"[Project]({FIRST}\n  (Title))",
            f'[Project][ref]\n\n[ref]: {FIRST} "Title"',
            f"[Project][]\n\n[Project]: {FIRST}",
            f"[Project]\n\n[Project]: {FIRST}",
            f"<{FIRST}>",
            FIRST,
            f"| Project |\n| --- |\n| [Project]({FIRST}) |",
            f"> - **[Project]({FIRST})**",
        ]
        for variant in variants:
            with self.subTest(markdown=variant):
                result, _, errors = self.compare(f"[Project]({FIRST})", variant)
                self.assertEqual(result, 0, errors)

    def test_comments_code_and_images_do_not_add_links(self):
        hidden = f"[Hidden]({SECOND})"
        variants = [
            f"<!-- {hidden} -->",
            f"Text <!-- {hidden} --> text",
            f"<!--\n{hidden}\n-->\n<!-- another comment -->",
            f"`{hidden}`",
            f"```markdown\n{hidden}\n```",
            f"~~~\n{hidden}\n~~~",
            f"    {hidden}",
            f"![Image]({SECOND})",
            f"[unused]: {SECOND}",
        ]
        visible = f"[Visible]({FIRST})"
        for variant in variants:
            with self.subTest(markdown=variant):
                result, _, errors = self.compare(visible, visible + "\n\n" + variant)
                self.assertEqual(result, 0, errors)

    def test_url_order_and_duplicates_matter(self):
        first, second = f"[A]({FIRST})", f"[B]({SECOND})"
        for english, german in [
            (first, second),
            (first + second, second + first),
            (first + first, first),
            (first, "No links"),
        ]:
            with self.subTest(english=english, german=german):
                result, output, errors = self.compare(english, german)
                self.assertEqual(result, 1)
                self.assertEqual(output, "")
                self.assertIn("weichen ab", errors)

    def test_diagnostics_retain_each_source_location(self):
        result, _, errors = self.compare(f"[A]({FIRST})", f"\n\n[B]({SECOND})")
        self.assertEqual(result, 1)
        self.assertIn(f"ab Zeile 1: {FIRST}", errors)
        self.assertIn(f"ab Zeile 3: {SECOND}", errors)

    def test_multiline_link_reports_start_of_text_block(self):
        self.english.write_text(f"Intro\n[A]({FIRST})", encoding="utf-8")
        self.assertEqual(github_links(self.english), [(1, FIRST)])

    def test_html_cannot_silently_pass(self):
        for html in [
            f'<a href="{SECOND}">Project</a>',
            f'<!-- before --> <a href="{SECOND}">Project</a> <!-- after -->',
            "Text <span>Project</span>",
        ]:
            with self.subTest(html=html):
                document = f"[A]({FIRST})\n\n{html}"
                result, output, errors = self.compare(document, document)
                self.assertEqual(result, 1)
                self.assertEqual(output, "")
                self.assertIn("HTML außer Kommentaren", errors)

    def test_empty_link_lists_fail(self):
        result, _, errors = self.compare("No links", "Keine Links")
        self.assertEqual(result, 1)
        self.assertIn("keine GitHub-Links", errors)

    def test_linked_image_counts_only_its_target(self):
        result, _, _ = self.compare(f"[A]({FIRST})", f"[![Image]({SECOND})]({FIRST})")
        self.assertEqual(result, 0)

    def test_cli_default_paths_work_from_another_directory(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/check_readme_links.py")],
            cwd=self.directory.name, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("20 GitHub-Links", result.stdout)

    def test_wrong_argument_count_fails(self):
        for arguments in [["one"], ["one", "two", "three"]]:
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(main(arguments), 2)
                self.assertIn("Aufruf:", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
