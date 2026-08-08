"""
build.py - Script de build e pré-renderização estática do portfólio.

Carrega portfolio-data.json, valida os dados via validator.py,
pré-renderiza o conteúdo textual semântico das seções em index.html,
gera metadados de SEO (meta tags, Open Graph, Twitter Card),
gera dados estruturados JSON-LD (Schema.org Person),
e produz sitemap.xml e robots.txt.

Este script é determinístico e idempotente.
"""

from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

from validator import validate_portfolio_data

# Garante suporte a UTF-8 no console do Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SITE_URL = "https://danieldpereira.github.io/"
SITE_IMAGE_URL = f"{SITE_URL}assets/imagens/Foto.jpeg"


def safe_text(val: Any) -> str:
    """Sanitiza e escapa texto para inserção segura no HTML."""
    if val is None:
        return ""
    return html.escape(str(val).strip())


def render_profile_cta(cta_list: List[Dict[str, str]]) -> str:
    if not isinstance(cta_list, list):
        return ""
    items = []
    for button in cta_list:
        url = safe_text(button.get("url", ""))
        label = safe_text(button.get("label", ""))
        btype = button.get("type", "")
        type_class = "btn btn-ghost" if btype == "ghost" else "btn btn-primary"
        target = "" if url.startswith("#") else ' target="_blank" rel="noopener noreferrer"'
        items.append(f'<a href="{url}" class="{type_class}"{target}>{label}</a>')
    return "\n            ".join(items)


def render_socials(socials_list: List[Dict[str, str]]) -> str:
    if not isinstance(socials_list, list):
        return ""
    items = []
    for soc in socials_list:
        url = safe_text(soc.get("url", ""))
        label = safe_text(soc.get("label", ""))
        icon = safe_text(soc.get("icon", ""))
        items.append(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="{label}">'
            f'<i class="{icon}"></i></a>'
        )
    return "\n          ".join(items)


def render_stats(stats_list: List[Dict[str, str]]) -> str:
    if not isinstance(stats_list, list):
        return ""
    items = []
    for stat in stats_list:
        val = safe_text(stat.get("value", ""))
        lbl = safe_text(stat.get("label", ""))
        items.append(
            f'<article class="stat-card">\n'
            f"            <strong>{val}</strong>\n"
            f"            <span>{lbl}</span>\n"
            f"          </article>"
        )
    return "\n          ".join(items)


def render_about(about: Dict[str, Any]) -> str:
    if not isinstance(about, dict):
        return ""
    greeting = safe_text(about.get("greeting", ""))
    paragraphs = about.get("paragraphs", [])
    highlights = about.get("highlights", [])

    p_html = "\n        ".join(
        [f"<p>{safe_text(p)}</p>" for p in paragraphs if isinstance(p, str)]
    )

    h_html = ""
    if isinstance(highlights, list) and highlights:
        chips = "\n            ".join(
            [f'<span class="chip">{safe_text(item)}</span>' for item in highlights]
        )
        h_html = f'<div class="chip-list">\n            {chips}\n          </div>'

    return (
        f'<p class="lead">{greeting}</p>\n'
        f"        {p_html}\n"
        f"        {h_html}".strip()
    )


def render_education(education_list: List[Dict[str, Any]]) -> str:
    if not isinstance(education_list, list):
        return ""
    items = []
    for item in education_list:
        degree = safe_text(item.get("degree", ""))
        institution = safe_text(item.get("institution", ""))
        period = safe_text(item.get("period", ""))
        itype = safe_text(item.get("type", ""))
        issuer = safe_text(item.get("issuer", ""))
        description = safe_text(item.get("description", ""))

        issuer_str = f" • {issuer}" if issuer else ""
        details = item.get("details", [])
        details_html = ""
        if isinstance(details, list) and details:
            lis = "".join([f"<li>{safe_text(d)}</li>" for d in details])
            details_html = f'\n          <ul class="achievements">{lis}</ul>'

        card = (
            f'<article class="education-item">\n'
            f"          <header>\n"
            f'            <h3 class="education-degree">{degree}</h3>\n'
            f'            <p class="education-institution muted">{institution}</p>\n'
            f'            <p class="muted">{period}</p>\n'
            f'            <p class="muted">{itype}{issuer_str}</p>\n'
            f"          </header>\n"
            f"          <p>{description}</p>{details_html}\n"
            f"        </article>"
        )
        items.append(card)
    return "\n        ".join(items)


def render_experiences(experiences_list: List[Dict[str, Any]]) -> str:
    if not isinstance(experiences_list, list):
        return ""
    items = []
    for item in experiences_list:
        title = safe_text(item.get("title", ""))
        period = safe_text(item.get("period", ""))
        itype = safe_text(item.get("type", ""))
        location = safe_text(item.get("location", ""))
        company = safe_text(item.get("company", ""))
        company_url = safe_text(item.get("companyUrl", ""))
        description = safe_text(item.get("description", ""))

        company_link = ""
        if company_url:
            company_link = (
                f'<a href="{company_url}" target="_blank" rel="noopener noreferrer" '
                f'class="company-link">{company} <i class="ri-external-link-line"></i></a>'
            )
        elif company:
            company_link = f'<span class="company-link">{company}</span>'

        achievements = item.get("achievements", [])
        ach_html = ""
        if isinstance(achievements, list) and achievements:
            lis = "\n            ".join([f"<li>{safe_text(a)}</li>" for a in achievements])
            ach_html = f'\n          <ul class="achievements">\n            {lis}\n          </ul>'

        techs = item.get("technologies", [])
        tech_html = ""
        if isinstance(techs, list) and techs:
            chips = "\n            ".join([f'<span class="chip">{safe_text(t)}</span>' for t in techs])
            tech_html = f'\n          <div class="chip-list">\n            {chips}\n          </div>'

        card = (
            f'<article class="timeline-item">\n'
            f"          <header>\n"
            f"            <h3>{title}</h3>\n"
            f'            <p class="muted">{period} • {itype} • {location}</p>\n'
            f"            {company_link}\n"
            f"          </header>\n"
            f"          <p>{description}</p>{ach_html}{tech_html}\n"
            f"        </article>"
        )
        items.append(card)
    return "\n        ".join(items)


def render_skills(skills_list: List[Dict[str, Any]]) -> str:
    if not isinstance(skills_list, list):
        return ""
    items = []
    for item in skills_list:
        icon = safe_text(item.get("icon", ""))
        alt = safe_text(item.get("alt", ""))
        name = safe_text(item.get("name", ""))
        cat = safe_text(item.get("category", "Tecnologia"))

        card = (
            f'<article class="skill-card">\n'
            f'          <img src="{icon}" alt="{alt}" loading="lazy">\n'
            f"          <h3>{name}</h3>\n"
            f"          <p>{cat}</p>\n"
            f"        </article>"
        )
        items.append(card)
    return "\n        ".join(items)


def render_projects(projects_list: List[Dict[str, Any]]) -> str:
    if not isinstance(projects_list, list):
        return ""
    items = []
    for idx, item in enumerate(projects_list):
        thumb = safe_text(item.get("thumbnail", ""))
        title = safe_text(item.get("title", ""))
        cat = safe_text(item.get("category", ""))
        year = safe_text(item.get("year", ""))
        desc = safe_text(item.get("description", ""))
        techs = item.get("technologies", [])

        chips_html = ""
        if isinstance(techs, list) and techs:
            chips = "\n            ".join([f'<span class="chip">{safe_text(t)}</span>' for t in techs[:3]])
            chips_html = f'\n          <div class="chip-list">\n            {chips}\n          </div>'

        card = (
            f'<article class="project-card" data-project-index="{idx}">\n'
            f'          <img src="{thumb}" alt="Thumbnail do projeto {title}" loading="lazy">\n'
            f'          <div class="project-body">\n'
            f'            <p class="project-meta">{cat} • {year}</p>\n'
            f"            <h3>{title}</h3>\n"
            f"            <p>{desc}</p>{chips_html}\n"
            f"          </div>\n"
            f'          <button class="btn btn-ghost project-open" data-project-index="{idx}">Ver detalhes</button>\n'
            f"        </article>"
        )
        items.append(card)
    return "\n        ".join(items)


def render_certificates(certificates_list: List[Dict[str, Any]]) -> str:
    if not isinstance(certificates_list, list):
        return ""
    items = []
    for item in certificates_list:
        title = safe_text(item.get("title", ""))
        url = safe_text(item.get("url", "#"))
        if url == "#":
            link_html = f'<span class="certificate-link muted">{title}</span>'
        else:
            link_html = (
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                f'class="certificate-link">{title} <i class="ri-external-link-line"></i></a>'
            )
        items.append(f"<li>\n          {link_html}\n        </li>")
    return "\n        ".join(items)


def render_contact_actions(profile: Dict[str, Any]) -> str:
    socials = profile.get("socials", [])
    email = profile.get("email", "")

    linkedin_url = ""
    if isinstance(socials, list):
        for soc in socials:
            if str(soc.get("label", "")).lower() == "linkedin":
                linkedin_url = safe_text(soc.get("url", ""))
                break

    actions = []
    if linkedin_url:
        actions.append(
            f'<a class="btn btn-primary" href="{linkedin_url}" target="_blank" rel="noopener noreferrer">'
            f'<i class="ri-linkedin-fill"></i> Conecte-se comigo!</a>'
        )
    if email:
        actions.append(
            f'<a class="btn btn-ghost" href="mailto:{safe_text(email)}">'
            f'<i class="ri-mail-send-line"></i> Enviar e-mail</a>'
        )
    return "\n          ".join(actions)


def build_json_ld(profile: Dict[str, Any]) -> str:
    name = profile.get("name", "Daniel Dias Pereira")
    hero_desc = profile.get("heroDescription", "")
    socials = profile.get("socials", [])
    same_as = []
    if isinstance(socials, list):
        for soc in socials:
            url = soc.get("url")
            if url and url.startswith("http"):
                same_as.append(url)

    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "url": SITE_URL,
        "image": SITE_IMAGE_URL,
        "jobTitle": "Desenvolvedor Backend, IA & Dados",
        "description": hero_desc,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "São José dos Campos",
            "addressRegion": "SP",
            "addressCountry": "BR",
        },
        "alumniOf": [
            {
                "@type": "EducationalOrganization",
                "name": "Fatec São José dos Campos - Prof. Jessen Vidal",
            }
        ],
        "sameAs": same_as,
    }
    return json.dumps(json_ld_data, ensure_ascii=False, indent=2)


def replace_container_content(html_content: str, element_id: str, new_inner_html: str) -> str:
    """Substitui o conteúdo interno do elemento com o id especificado mantendo a tag intacta."""
    pattern = re.compile(
        rf'(<([a-z0-9]+)\b[^>]*\bid=["\']{re.escape(element_id)}["\'][^>]*>)(.*?)(</\2>)',
        re.DOTALL | re.IGNORECASE,
    )
    
    def replacer(match):
        open_tag = match.group(1)
        close_tag = match.group(4)
        if new_inner_html.strip():
            return f"{open_tag}\n        {new_inner_html.strip()}\n      {close_tag}"
        else:
            return f"{open_tag}{close_tag}"

    return pattern.sub(replacer, html_content)


def generate_sitemap(portfolio_path: Path, output_path: Path):
    """Gera sitemap.xml determinístico com data de modificação baseada no JSON."""
    mtime = datetime.fromtimestamp(portfolio_path.stat().st_mtime, tz=timezone.utc)
    lastmod = mtime.strftime("%Y-%m-%d")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    output_path.write_text(sitemap_content, encoding="utf-8")
    print(f"[OK] sitemap.xml gerado com sucesso! ({output_path})")


def generate_robots(output_path: Path):
    """Gera robots.txt apontando para o sitemap oficial."""
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}sitemap.xml
"""
    output_path.write_text(robots_content, encoding="utf-8")
    print(f"[OK] robots.txt gerado com sucesso! ({output_path})")


def update_head_seo(html_content: str, profile: Dict[str, Any]) -> str:
    """Atualiza a seção <head> do index.html com metadados de SEO, OG, Twitter Card e JSON-LD."""
    name = safe_text(profile.get("name", "Daniel Dias Pereira"))
    eyebrow = safe_text(profile.get("heroEyebrow", "Dados • IA • Backend"))
    desc = safe_text(profile.get("heroDescription", ""))
    
    page_title = f"{name} | {eyebrow}"
    json_ld_str = build_json_ld(profile)

    new_head_meta = f"""  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>

  <meta name="description" content="{desc}">
  <meta name="author" content="{name}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{SITE_URL}">

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{SITE_IMAGE_URL}">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:site_name" content="{name} | Portfólio">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{SITE_IMAGE_URL}">

  <!-- Schema.org JSON-LD -->
  <script type="application/ld+json">
{json_ld_str}
  </script>

  <link rel="icon" type="image/png" sizes="32x32" href="./assets/favicon_io/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="./assets/favicon_io/favicon-16x16.png">
  <link rel="manifest" href="./assets/favicon_io/site.webmanifest">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">

  <link rel="stylesheet" href="./style/style.css">"""

    head_pattern = re.compile(r"<head>(.*?)</head>", re.DOTALL | re.IGNORECASE)
    return head_pattern.sub(f"<head>\n{new_head_meta}\n</head>", html_content)


def run_build(
    data_path: str = "portfolio-data.json",
    index_path: str = "index.html",
) -> bool:
    """Executa a pipeline completa de pré-renderização e SEO estático."""
    data_file = Path(data_path)
    index_file = Path(index_path)

    if not data_file.exists():
        print(f"ERRO: Arquivo de dados '{data_path}' não foi encontrado.")
        return False

    if not index_file.exists():
        print(f"ERRO: Arquivo HTML '{index_path}' não foi encontrado.")
        return False

    # 1. Validação de dados
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERRO: Falha ao ler JSON '{data_path}': {e}")
        return False

    errors = validate_portfolio_data(data)
    if errors:
        print(f"\n[BUILD FALHOU] {len(errors)} erro(s) encontrados no JSON:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[1/4] Dados validados com sucesso.")

    # 2. Leitura do index.html
    html_content = index_file.read_text(encoding="utf-8")

    profile = data.get("profile", {})
    about = data.get("about", {})
    education = data.get("education", [])
    experiences = data.get("experiences", [])
    skills = data.get("skills", [])
    projects = data.get("projects", [])
    certificates = data.get("certificates", [])

    # 3. Pré-renderização de HTML das seções
    html_content = update_head_seo(html_content, profile)

    html_content = replace_container_content(html_content, "brand-name", safe_text(profile.get("name", "")))
    html_content = replace_container_content(html_content, "hero-eyebrow", safe_text(profile.get("heroEyebrow", "")))
    html_content = replace_container_content(html_content, "hero-title", safe_text(profile.get("heroTitle") or profile.get("name", "")))
    html_content = replace_container_content(html_content, "hero-description", safe_text(profile.get("heroDescription", "")))

    html_content = replace_container_content(html_content, "hero-actions", render_profile_cta(profile.get("cta", [])))
    html_content = replace_container_content(html_content, "socials-list", render_socials(profile.get("socials", [])))
    html_content = replace_container_content(html_content, "stats-grid", render_stats(profile.get("stats", [])))

    html_content = replace_container_content(html_content, "about-content", render_about(about))
    html_content = replace_container_content(html_content, "education-list", render_education(education))
    html_content = replace_container_content(html_content, "experience-list", render_experiences(experiences))
    html_content = replace_container_content(html_content, "skills-grid", render_skills(skills))
    html_content = replace_container_content(html_content, "projects-grid", render_projects(projects))
    html_content = replace_container_content(html_content, "certificates-list", render_certificates(certificates))

    html_content = replace_container_content(html_content, "contact-message", safe_text(profile.get("contactMessage", "")))
    html_content = replace_container_content(html_content, "contact-actions", render_contact_actions(profile))
    html_content = replace_container_content(html_content, "footer-text", safe_text(profile.get("footerText", "")))
    html_content = replace_container_content(html_content, "footer-socials", render_socials(profile.get("socials", [])))

    # Escreve o index.html atualizado
    index_file.write_text(html_content, encoding="utf-8")
    print(f"[2/4] Conteúdo pré-renderizado injetado em '{index_path}'.")

    # 4. Geração de Sitemap e Robots
    generate_sitemap(data_file, Path("sitemap.xml"))
    generate_robots(Path("robots.txt"))

    print("\n[SUCESSO] Build estático do portfólio concluído com sucesso!")
    return True


if __name__ == "__main__":
    success = run_build()
    sys.exit(0 if success else 1)
