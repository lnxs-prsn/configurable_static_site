#!/usr/bin/env python3
"""
Build script for Tusmo ry website.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_yaml(path):
    """Load a YAML file, return empty dict if missing."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_markdown(path):
    """Load a Markdown file, return empty string if missing."""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def md_to_html(md_text):
    """Convert Markdown to HTML."""
    return markdown.markdown(md_text, extensions=["extra"])


def strip_html_tags(html_text):
    """Strip HTML tags from text."""
    clean = re.sub(r"<[^>]+>", "", html_text)
    return clean


def get_first_paragraph(md_text):
    """Get the first paragraph of Markdown text (before any blank line)."""
    lines = md_text.strip().split("\n")
    paragraph_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            break
        paragraph_lines.append(stripped)
    return " ".join(paragraph_lines)


def image_exists(slot_name):
    """Check if an image file exists for the given slot (checks .jpg and .png)."""
    for ext in [".jpg", ".png"]:
        if os.path.exists(f"images/{slot_name}{ext}"):
            return True
    return False


def build_context():
    """Build the full Jinja2 context dict for all pages."""
    # 1. Read config
    config = load_yaml("config.yml")

    # 2. Read contact details
    contact = load_yaml("content/yhteystiedot.yml")

    # 3. Read events
    events_data = load_yaml("content/tapahtumat.yml")
    events = events_data.get("events", [])

    # 4. Read Markdown content files
    home_md = load_markdown("content/etusivu.md")
    about_md = load_markdown("content/tietoa-jarjestosta.md")
    toiminta_md = load_markdown("content/toiminta.md")

    home_html = md_to_html(home_md)
    about_html = md_to_html(about_md)
    toiminta_html = md_to_html(toiminta_md)

    # 5. Scan images
    image_slots = [
        "home-1", "home-2", "about-1", "about-2",
        "toiminta-1", "toiminta-2", "tapahtumat-1", "yhteystiedot-1",
    ]
    images = {slot: image_exists(slot) for slot in image_slots}

    # 6. Build nav_pages
    page_definitions = [
        {"key": "home", "title": "Etusivu", "url": "/", "toggle_key": None, "always_on": True},
        {"key": "about", "title": "Tietoa järjestöstä", "url": "/tietoa-jarjestosta/", "toggle_key": "about", "always_on": False},
        {"key": "toiminta", "title": "Toiminta", "url": "/toiminta/", "toggle_key": "toiminta", "always_on": False},
        {"key": "tapahtumat", "title": "Tapahtumat", "url": "/tapahtumat/", "toggle_key": "tapahtumat", "always_on": False},
        {"key": "yhteystiedot", "title": "Yhteystiedot", "url": "/yhteystiedot/", "toggle_key": None, "always_on": True},
    ]

    nav_pages = []
    for page in page_definitions:
        if page["always_on"]:
            nav_pages.append({"title": page["title"], "url": page["url"], "key": page["key"]})
        elif page["toggle_key"]:
            if config.get("pages", {}).get(page["toggle_key"], False):
                nav_pages.append({"title": page["title"], "url": page["url"], "key": page["key"]})

    # 7. Social links
    social_config = config.get("social", {})
    has_social = any(
        isinstance(v, str) and v.strip() != ""
        for v in social_config.values()
    )
    social_links = []
    for platform, url in social_config.items():
        if isinstance(url, str) and url.strip() != "":
            social_links.append({"platform": platform, "url": url})

    # 8. Current year
    current_year = datetime.now().year

    # 9. Meta descriptions
    home_first_para = get_first_paragraph(home_md)
    home_meta = strip_html_tags(md_to_html(home_first_para))[:160]

    about_first_para = get_first_paragraph(about_md)
    about_meta = strip_html_tags(md_to_html(about_first_para))[:160]

    toiminta_first_para = get_first_paragraph(toiminta_md)
    toiminta_meta = strip_html_tags(md_to_html(toiminta_first_para))[:160]

    # OG image helper
    def get_og_image(page_key):
        page_image_map = {
            "home": "home-1",
            "about": "about-1",
            "toiminta": "toiminta-1",
            "tapahtumat": "tapahtumat-1",
            "yhteystiedot": "yhteystiedot-1",
        }
        slot = page_image_map.get(page_key)
        if slot and images.get(slot):
            return f"{config['site']['url']}/static/images/{slot}.jpg"
        # Fallback to about-1
        if images.get("about-1"):
            return f"{config['site']['url']}/static/images/about-1.jpg"
        return None

    # Build per-page contexts
    contexts = {}
    page_meta_map = {
        "home": {
            "page_title": "Tusmo ry",
            "page_url": "/",
            "content_html": home_html,
            "meta_description": home_meta,
            "events": [],
            "template": "home.html",
        },
        "about": {
            "page_title": "Tietoa järjestöstä",
            "page_url": "/tietoa-jarjestosta/",
            "content_html": about_html,
            "meta_description": about_meta,
            "events": [],
            "template": "about.html",
        },
        "toiminta": {
            "page_title": "Toiminta",
            "page_url": "/toiminta/",
            "content_html": toiminta_html,
            "meta_description": toiminta_meta,
            "events": [],
            "template": "toiminta.html",
        },
        "tapahtumat": {
            "page_title": "Tapahtumat",
            "page_url": "/tapahtumat/",
            "content_html": "",
            "meta_description": "Tusmo ry:n tapahtumat Vantaalla.",
            "events": events,
            "template": "tapahtumat.html",
        },
        "yhteystiedot": {
            "page_title": "Yhteystiedot",
            "page_url": "/yhteystiedot/",
            "content_html": "",
            "meta_description": "Ota yhteyttä Tusmo ry:hyn. Osoite: Leisikuja 7A, 01600 Vantaa.",
            "events": [],
            "template": "yhteystiedot.html",
        },
    }

    for page_key, page_data in page_meta_map.items():
        og_image = get_og_image(page_key)
        context = {
            "config": config,
            "contact": contact,
            "current_page": page_key,
            "current_year": current_year,
            "nav_pages": nav_pages,
            "has_social": has_social,
            "social_links": social_links,
            "content_html": page_data["content_html"],
            "events": page_data["events"],
            "images": images,
            "page_url": page_data["page_url"],
            "page_title": page_data["page_title"],
            "meta_description": page_data["meta_description"],
            "og_image": og_image,
        }
        contexts[page_key] = context

    return contexts


def compile_tailwind():
    """Invoke Tailwind CSS CLI to compile input.css to output CSS."""
    tailwind_bin = "bin/tailwindcss"
    if not os.path.exists(tailwind_bin):
        print("ERROR: Tailwind binary not found at bin/tailwindcss", file=sys.stderr)
        print("Run ./build.sh to auto-download it, or place it manually.", file=sys.stderr)
        sys.exit(1)

    if not os.access(tailwind_bin, os.X_OK):
        print("ERROR: Tailwind binary is not executable. Run: chmod +x bin/tailwindcss", file=sys.stderr)
        sys.exit(1)

    os.makedirs("output/static/css", exist_ok=True)
    result = subprocess.run(
        [tailwind_bin, "-i", "src/input.css", "-o", "output/static/css/main.css", "--minify"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Tailwind compilation failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print("Tailwind CSS compiled successfully.")


def copy_assets():
    """Copy fonts and images to output directory."""
    # Copy fonts
    if os.path.exists("fonts"):
        os.makedirs("output/static/fonts", exist_ok=True)
        for fname in os.listdir("fonts"):
            if fname.endswith(".woff2"):
                shutil.copy2(f"fonts/{fname}", f"output/static/fonts/{fname}")

    # Copy images
    if os.path.exists("images"):
        os.makedirs("output/static/images", exist_ok=True)
        for fname in os.listdir("images"):
            if fname.endswith(".jpg") or fname.endswith(".png") or fname == "favicon.svg":
                shutil.copy2(f"images/{fname}", f"output/static/images/{fname}")


def render_pages(env, contexts):
    """Render all enabled page templates and write to output."""
    page_output_map = {
        "home": "output/index.html",
        "about": "output/tietoa-jarjestosta/index.html",
        "toiminta": "output/toiminta/index.html",
        "tapahtumat": "output/tapahtumat/index.html",
        "yhteystiedot": "output/yhteystiedot/index.html",
    }

    # Determine which pages are enabled
    config = contexts["home"]["config"]
    enabled_pages = {"home", "yhteystiedot"}  # Always on
    for page_key in ["about", "toiminta", "tapahtumat"]:
        if config.get("pages", {}).get(page_key, False):
            enabled_pages.add(page_key)

    for page_key in enabled_pages:
        context = contexts[page_key]
        template_name = context.get("template", f"{page_key}.html")

        # Check if template exists
        template_path = f"templates/{template_name}"
        if not os.path.exists(template_path):
            print(f"Skipping {page_key}: template {template_name} not found")
            continue

        template = env.get_template(template_name)
        html = template.render(**context)

        output_path = page_output_map[page_key]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Rendered: {output_path}")

    # Render 404
    template = env.get_template("404.html")
    # Use home context for 404
    html = template.render(**contexts["home"])
    with open("output/404.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Rendered: output/404.html")


def write_sitemap(contexts):
    """Generate sitemap.xml from all enabled pages."""
    config = contexts["home"]["config"]
    base_url = config["site"]["url"]
    today = datetime.now().strftime("%Y-%m-%d")

    enabled_pages = {"home": "/", "yhteystiedot": "/yhteystiedot/"}
    for page_key in ["about", "toiminta", "tapahtumat"]:
        if config.get("pages", {}).get(page_key, False):
            url_map = {
                "about": "/tietoa-jarjestosta/",
                "toiminta": "/toiminta/",
                "tapahtumat": "/tapahtumat/",
            }
            enabled_pages[page_key] = url_map[page_key]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page_key, url_path in enabled_pages.items():
        lines.append("  <url>")
        lines.append(f"    <loc>{base_url}{url_path}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open("output/sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Written: output/sitemap.xml")


def write_robots(contexts):
    """Generate robots.txt."""
    config = contexts["home"]["config"]
    base_url = config["site"]["url"]

    content = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""
    with open("output/robots.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Written: output/robots.txt")


def main():
    # Step 1: Delete output/ entirely, recreate it
    if os.path.exists("output"):
        shutil.rmtree("output")
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/static/css", exist_ok=True)
    os.makedirs("output/static/fonts", exist_ok=True)
    os.makedirs("output/static/images", exist_ok=True)

    # Step 2: Read all data
    contexts = build_context()

    # Step 3: Compile Tailwind CSS
    compile_tailwind()

    # Step 4: Copy assets
    copy_assets()

    # Step 5: Render templates
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html"]),
    )
    render_pages(env, contexts)

    # Step 6: Write sitemap and robots.txt
    write_sitemap(contexts)
    write_robots(contexts)

    print("\nBuild complete. Output written to output/")


if __name__ == "__main__":
    main()
