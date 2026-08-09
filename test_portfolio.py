"""
test_portfolio.py - Suíte de testes automatizados para o sistema de pré-renderização,
validação de dados e metadados SEO do portfólio.
"""

import html
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from build import (
    SITE_URL,
    build_json_ld,
    render_about,
    render_certificates,
    render_education,
    render_experiences,
    render_projects,
    render_skills,
    run_build,
    update_head_seo,
)
from validator import validate_portfolio_data


class TestValidator(unittest.TestCase):
    def setUp(self):
        with open("portfolio-data.json", "r", encoding="utf-8") as f:
            self.valid_data = json.load(f)

    def test_valid_portfolio_data(self):
        errors = validate_portfolio_data(self.valid_data)
        self.assertEqual(errors, [], "O JSON válido do portfólio não deve retornar nenhum erro.")

    def test_missing_section(self):
        invalid_data = dict(self.valid_data)
        del invalid_data["profile"]
        errors = validate_portfolio_data(invalid_data)
        self.assertTrue(any("profile" in err for err in errors))

    def test_empty_profile_field(self):
        invalid_data = json.loads(json.dumps(self.valid_data))
        invalid_data["profile"]["name"] = ""
        errors = validate_portfolio_data(invalid_data)
        self.assertTrue(any("profile.name" in err for err in errors))

    def test_invalid_project_field(self):
        invalid_data = json.loads(json.dumps(self.valid_data))
        invalid_data["projects"][0]["title"] = ""
        errors = validate_portfolio_data(invalid_data)
        self.assertTrue(any("projects[0].title" in err for err in errors))

    def test_invalid_section_type(self):
        invalid_data = json.loads(json.dumps(self.valid_data))
        invalid_data["skills"] = "não é uma lista"
        errors = validate_portfolio_data(invalid_data)
        self.assertTrue(any("skills" in err for err in errors))


class TestBuildHTMLGenerators(unittest.TestCase):
    def setUp(self):
        with open("portfolio-data.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_render_about(self):
        html_out = render_about(self.data["about"])
        self.assertIn('<p class="lead">', html_out)
        self.assertIn(html.escape(self.data["about"]["greeting"]), html_out)
        for paragraph in self.data["about"]["paragraphs"]:
            self.assertIn(html.escape(paragraph), html_out)

    def test_render_education(self):
        html_out = render_education(self.data["education"])
        self.assertIn('<article class="education-item">', html_out)
        for item in self.data["education"]:
            self.assertIn(html.escape(item["degree"]), html_out)
            self.assertIn(html.escape(item["institution"]), html_out)

    def test_render_experiences(self):
        html_out = render_experiences(self.data["experiences"])
        self.assertIn('<article class="timeline-item">', html_out)
        for item in self.data["experiences"]:
            self.assertIn(html.escape(item["title"]), html_out)
            self.assertIn(html.escape(item["company"]), html_out)

    def test_render_skills(self):
        html_out = render_skills(self.data["skills"])
        self.assertIn('<article class="skill-card">', html_out)
        for item in self.data["skills"]:
            self.assertIn(html.escape(item["name"]), html_out)

    def test_render_projects(self):
        html_out = render_projects(self.data["projects"])
        self.assertIn('<article class="project-card"', html_out)
        self.assertIn('data-project-index="0"', html_out)
        for idx, item in enumerate(self.data["projects"]):
            self.assertIn(html.escape(item["title"]), html_out)
            self.assertIn(f'data-project-index="{idx}"', html_out)

    def test_render_certificates(self):
        html_out = render_certificates(self.data["certificates"])
        self.assertIn("<li>", html_out)
        for item in self.data["certificates"]:
            self.assertIn(html.escape(item["title"]), html_out)


class TestSEOAndMetadata(unittest.TestCase):
    def setUp(self):
        with open("portfolio-data.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_build_json_ld_validity(self):
        json_ld_str = build_json_ld(self.data["profile"])
        parsed = json.loads(json_ld_str)
        self.assertEqual(parsed["@context"], "https://schema.org")
        self.assertEqual(parsed["@type"], "Person")
        self.assertEqual(parsed["name"], self.data["profile"]["name"])
        self.assertEqual(parsed["url"], SITE_URL)
        self.assertIsInstance(parsed["sameAs"], list)

    def test_update_head_seo(self):
        base_html = "<html><head><title>Antigo</title></head><body></body></html>"
        updated_html = update_head_seo(base_html, self.data["profile"])

        self.assertIn("<title>Daniel Dias Pereira |", updated_html)
        self.assertIn('<meta name="description"', updated_html)
        self.assertIn('<meta name="author" content="Daniel Dias Pereira">', updated_html)
        self.assertIn('<link rel="canonical" href="https://danieldpereira.github.io/">', updated_html)
        self.assertIn('<meta property="og:type" content="website">', updated_html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', updated_html)
        self.assertIn('<script type="application/ld+json">', updated_html)


class TestBuildPipelineAndIdempotency(unittest.TestCase):
    def test_run_build(self):
        success = run_build("portfolio-data.json", "index.html")
        self.assertTrue(success, "O build estático deve ser executado com sucesso.")

        robots_path = Path("robots.txt")
        sitemap_path = Path("sitemap.xml")
        index_path = Path("index.html")

        self.assertTrue(robots_path.exists(), "robots.txt deve existir.")
        self.assertTrue(sitemap_path.exists(), "sitemap.xml deve existir.")

        # Teste do conteúdo do robots.txt
        robots_content = robots_path.read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots_content)
        self.assertIn("Sitemap: https://danieldpereira.github.io/sitemap.xml", robots_content)

        # Teste de validade do sitemap.xml
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("urlset"))
        loc = root.find("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.text, "https://danieldpereira.github.io/")

        # Teste de conteúdo no index.html
        index_content = index_path.read_text(encoding="utf-8")
        self.assertIn("Daniel Dias Pereira", index_content)
        self.assertIn('id="projects-grid"', index_content)
        self.assertIn('data-project-index="0"', index_content)

    def test_build_idempotency(self):
        # Primeira execução
        run_build("portfolio-data.json", "index.html")
        index_run1 = Path("index.html").read_text(encoding="utf-8")
        sitemap_run1 = Path("sitemap.xml").read_text(encoding="utf-8")
        robots_run1 = Path("robots.txt").read_text(encoding="utf-8")

        # Segunda execução
        run_build("portfolio-data.json", "index.html")
        index_run2 = Path("index.html").read_text(encoding="utf-8")
        sitemap_run2 = Path("sitemap.xml").read_text(encoding="utf-8")
        robots_run2 = Path("robots.txt").read_text(encoding="utf-8")

        self.assertEqual(index_run1, index_run2, "Executar o build duas vezes deve produzir o index.html exatamente idêntico.")
        self.assertEqual(sitemap_run1, sitemap_run2, "Executar o build duas vezes deve produzir o sitemap.xml exatamente idêntico.")
        self.assertEqual(robots_run1, robots_run2, "Executar o build duas vezes deve produzir o robots.txt exatamente idêntico.")


if __name__ == "__main__":
    unittest.main()
