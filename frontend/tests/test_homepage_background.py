"""Regression: Task 15 long results must not change homepage skyline sizing."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class HeroBackgroundSizingTests(unittest.TestCase):
    def test_both_entry_points_use_bounded_background_layer(self):
        for page in ("index.html", "frontend/index.html"):
            with self.subTest(page=page):
                source = (ROOT / page).read_text(encoding="utf-8")
                hero = source.split("    .hero {", 1)[1].split("    .hero::after {", 1)[0]
                bounded = source.split("    .hero::after {", 1)[1].split("    .hero::before {", 1)[0]
                self.assertIn("background: var(--navy-deep)", hero)
                self.assertNotIn("background-size: cover", hero)
                self.assertIn("height: clamp(760px, 75vw, 1120px)", bounded)
                self.assertIn("linear-gradient(to bottom", bounded)
                self.assertIn("background-size: cover", bounded)
                self.assertIn("height: clamp(650px, 145vw, 880px)", source)
                self.assertNotIn(".hero::after { display: none; }", source)
                self.assertIn('id="problem-intake"', source)
                self.assertIn('src="./', source)

    def test_assets_keep_separate_relative_routes(self):
        public = (ROOT / "index.html").read_text(encoding="utf-8")
        local = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        self.assertIn('url("./frontend/assets/sg-skyline.webp")', public)
        self.assertIn('url("./assets/sg-skyline.webp")', local)


if __name__ == "__main__":
    unittest.main()
