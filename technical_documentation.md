# Technical Documentation

Detailed reference for developers who want to understand, modify, or extend this project.

---

## Architecture overview

The project is a **build-time static site generator** written in Python. There is no runtime server, no CMS, and no database. Everything runs once at build time:

```
config.yml  ─┐
content/*.md ─┤              ┌─ output/index.html
content/*.yml ┤─ build.py ──►├─ output/*/index.html
templates/   ─┤              ├─ output/static/css/main.css
images/       ┤              ├─ output/static/images/*
src/input.css ┘              ├─ output/sitemap.xml
                             └─ output/robots.txt
```

The output is a folder of plain HTML, CSS, and image files deployable on any static host.

---

## Build pipeline — `build.py`

The `main()` function runs these steps in order:

### Step 1 — Clean output
```python
shutil.rmtree("output")
os.makedirs("output", ...)
```
The entire `output/` directory is deleted and recreated on every build. There is no incremental build.

### Step 2 — Build context (`build_context()`)
Reads all data sources and returns a dict called `contexts` keyed by page name (`"home"`, `"about"`, etc.). Every page gets a complete context dict so templates can access any value.

Key values in every page context:

| Key | Source | Description |
|---|---|---|
| `config` | `config.yml` | Full parsed config dict |
| `contact` | `content/yhteystiedot.yml` | Name, address, phone, email |
| `nav_pages` | computed | List of `{title, url, key}` for enabled pages |
| `current_page` | constant per page | String key matching `nav_pages[*].key` |
| `content_html` | Markdown → HTML | Rendered prose for the page |
| `events` | `content/tapahtumat.yml` | List of event dicts (tapahtumat page only) |
| `images` | filesystem scan | Dict of slot → bool (True if file exists) |
| `social_links` | `config.yml` | List of `{platform, url}` (only non-empty) |
| `has_social` | computed | True if any social URL is set |
| `meta_description` | first paragraph | Auto-extracted, stripped of HTML, capped at 160 chars |
| `og_image` | computed | Absolute URL to page-specific or fallback image |
| `current_year` | `datetime.now()` | Used in footer copyright |

### Step 3 — Compile Tailwind CSS (`compile_tailwind()`)
Calls the standalone Tailwind v4 binary at `bin/tailwindcss`:
```
bin/tailwindcss -i src/input.css -o output/static/css/main.css --minify
```
The binary scans `templates/**/*.html` for class names (declared with `@source` in `input.css`). Any class used in a template is included in the output CSS; everything else is purged.

### Step 4 — Copy assets (`copy_assets()`)
- `fonts/*.woff2` → `output/static/fonts/`
- `images/*.jpg`, `images/*.png`, `images/favicon.svg` → `output/static/images/`

### Step 5 — Render templates (`render_pages()`)
Uses Jinja2 with `FileSystemLoader("templates")` and `autoescape` enabled for HTML. For each enabled page:
1. Determines whether the page is enabled (from `config.yml` toggles)
2. Loads the correct template file
3. Calls `template.render(**context)`
4. Writes the result to `output/<slug>/index.html` (or `output/index.html` for home)

The 404 page is always rendered using the home page context.

### Step 6 — Sitemap and robots.txt
`write_sitemap()` generates a standard `sitemap.xml` containing only the enabled pages. `write_robots()` writes a permissive `robots.txt` pointing to the sitemap.

---

## Page enabling logic

Two pages are always built: `home` and `yhteystiedot`.

The other three are enabled when `config.yml` has:
```yaml
pages:
  about: true      # → /tietoa-jarjestosta/
  toiminta: true   # → /toiminta/
  tapahtumat: true # → /tapahtumat/
```

Setting a value to `false` (or omitting the key) causes:
- The page HTML file is not written
- The page is removed from `nav_pages`, so it disappears from the nav and footer
- The page URL is removed from `sitemap.xml`

This logic runs in `build_context()` when building `nav_pages`, and again in `render_pages()` to decide which templates to render, and again in `write_sitemap()`.

---

## Templates

### Inheritance chain

All page templates extend `_base.html`:

```
_base.html          ← defines: <head>, nav, <main>{% block content %}, footer, Alpine, HTMX
  home.html
  about.html
  toiminta.html
  tapahtumat.html
  yhteystiedot.html   ← includes _partials/form-success.html, _partials/form-error.html
  404.html
```

### `_base.html` structure

- `<head>`: charset, viewport, meta description, title, favicon, CSS link, Open Graph tags, HTMX CDN script
- `<nav>`: sticky navbar with desktop links and Alpine.js-powered mobile hamburger/tray. The active page gets a gold left border (`border-l-4 border-accent`).
- `<main>{% block content %}{% endblock %}`: page-specific content
- `<footer>`: 2- or 3-column grid (contact info, quick links, optionally social links). Column count is decided by `has_social`.
- Alpine.js CDN script (deferred)
- `{% block scripts %}`: for page-specific JS

### Image sections

Each page template guards image sections with:
```jinja2
{% if images['slot-name'] %}
  <img src="/static/images/slot-name.jpg" ...>
{% endif %}
```

The `images` dict is populated in `build_context()` by `image_exists()`, which checks for both `.jpg` and `.png` extensions. If neither file is present the block is skipped entirely.

### Contact form (yhteystiedot.html)

The form uses HTMX:
```html
<form hx-post="{{ config.form_endpoint }}" hx-swap="none" hx-indicator="#form-spinner"
      hx-on::after-request="...reveal success or error div...">
```

- `hx-swap="none"` — HTMX does not update the DOM from the response body; the form handles its own UI via `hx-on::after-request`.
- `hx-indicator` — shows a spinner SVG while the request is in flight (HTMX adds/removes `htmx-request` class).
- On success (HTTP 200): the form hides itself, shows `#form-success`.
- On failure (any non-200): shows `#form-error`.
- The success and error partials are pre-rendered inside hidden `<div>` elements; no HTMX swap is needed.
- If `form_endpoint` is empty in config, the submit button gets `disabled` and a tooltip.

---

## Styling — `src/input.css`

### Theme tokens (Tailwind v4 `@theme`)

All brand colours are CSS custom properties declared in `@theme`. Change a hex value and rebuild — Tailwind rewrites every utility that references that token.

```css
@theme {
  --color-primary:        #0f4c4c;  /* deep teal */
  --color-primary-light:  #1a6b6b;
  --color-primary-dark:   #0a3333;
  --color-background:     #f7f5f0;  /* warm off-white */
  --color-surface:        #ffffff;
  --color-muted:          #e5e1d8;
  --color-text-secondary: #6b6560;
  --color-text-primary:   #1a1a1a;
  --color-accent:         #c9a84c;  /* warm gold */
  --color-accent-hover:   #b8983f;
  --color-success:        #2d7a3e;
  --color-error:          #b91c1c;
  --font-sans: "Noto Sans", ui-sans-serif, system-ui, sans-serif;
}
```

### Custom classes

**`.bg-texture`** — repeating SVG background using a Girih lattice pattern. The SVG is inlined as a data URI. `--texture-opacity: 0.02` controls how visible the pattern is (very subtle by default).

**`.prose`** — typography styles for Markdown-rendered HTML. Applied as a CSS `@layer base` block with element selectors (`h1`, `h2`, `p`, `ul`, `a`, `strong`). No `@tailwindcss/typography` plugin is used — this avoids needing npm entirely.

### Fonts

Two `@font-face` rules load Noto Sans 400 and 700 weight from `output/static/fonts/`. The declarations appear before `@import "tailwindcss"` — this is required by Tailwind v4's build order.

Font files must be placed in `app/fonts/` as `.woff2` files named `noto-sans-400.woff2` and `noto-sans-700.woff2`.

---

## Content files reference

### `content/etusivu.md`, `tietoa-jarjestosta.md`, `toiminta.md`

Plain Markdown. Converted to HTML using the Python `markdown` library with the `extra` extension (adds tables, footnotes, attribute lists, etc.).

The first paragraph (text before the first blank line) is extracted with `get_first_paragraph()`, converted to HTML, then stripped of tags with `strip_html_tags()` to produce the `meta_description` (capped at 160 characters).

### `content/tapahtumat.yml`

```yaml
events:
  - name: "Required string"
    date: "Optional — any string format"
    description: "Optional string"
    location: "Optional string"
```

The template renders a card per event. Fields `date`, `description`, and `location` are individually gated with `{% if event.field %}`, so any can be omitted.

### `content/yhteystiedot.yml`

```yaml
name: "Organisation name"
mission: "Short description"
address: "Street, City"
phone: "Number"
email: "address@example.fi"
```

Used in both `yhteystiedot.html` (contact page) and `_base.html` (footer).

---

## Adding a new page

1. **Add content** — create `content/mypage.md` (or a `.yml` if structured data is needed).

2. **Add a toggle** in `config.yml`:
   ```yaml
   pages:
     mypage: true
   ```

3. **Register the page** in `build.py`:

   In `page_definitions` (inside `build_context()`):
   ```python
   {"key": "mypage", "title": "My Page", "url": "/mypage/", "toggle_key": "mypage", "always_on": False},
   ```

   In `page_meta_map`:
   ```python
   "mypage": {
       "page_title": "My Page",
       "page_url": "/mypage/",
       "content_html": md_to_html(load_markdown("content/mypage.md")),
       "meta_description": "...",
       "events": [],
       "template": "mypage.html",
   },
   ```

   In `page_output_map` (inside `render_pages()`):
   ```python
   "mypage": "output/mypage/index.html",
   ```

   In the `enabled_pages` loop (inside `render_pages()`) and `write_sitemap()`:
   ```python
   for page_key in ["about", "toiminta", "tapahtumat", "mypage"]:
       if config.get("pages", {}).get(page_key, False):
           enabled_pages.add(page_key)
   ```
   (and the same for the sitemap url_map)

4. **Create the template** at `templates/mypage.html`:
   ```jinja2
   {% extends "_base.html" %}
   {% block content %}
   <section class="bg-background bg-texture py-12 px-4 sm:px-6 lg:px-8">
     <div class="max-w-prose mx-auto">
       <div class="prose">{{ content_html | safe }}</div>
     </div>
   </section>
   {% endblock %}
   ```

5. **Rebuild** — `./build.sh`

---

## Adding a new image slot

1. Add the image file to `app/images/` following the naming convention (e.g. `mypage-1.jpg`).

2. Add the slot name to `image_slots` in `build_context()`:
   ```python
   image_slots = [
       "home-1", "home-2", "about-1", "about-2",
       "toiminta-1", "toiminta-2", "tapahtumat-1", "yhteystiedot-1",
       "mypage-1",  # new
   ]
   ```

3. Use it in a template:
   ```jinja2
   {% if images['mypage-1'] %}
   <img src="/static/images/mypage-1.jpg" alt="..." loading="lazy">
   {% endif %}
   ```

---

## Adding a social platform

The supported platforms (`facebook`, `instagram`, `youtube`, `twitter`, `tiktok`) have SVG icons hardcoded in `_base.html` (footer social links block). To add a new platform:

1. Add the key to `config.yml`:
   ```yaml
   social:
     linkedin: "https://linkedin.com/company/..."
   ```

2. Add the SVG icon case in `_base.html` inside the `{% for link in social_links %}` block:
   ```jinja2
   {% elif link.platform == 'linkedin' %}
   <svg ...>...</svg>
   ```

If no icon is added, the platform name still renders as text with a link — it won't break the build.

---

## Changing brand colours

All colours are in `src/input.css` under `@theme`. Edit and rebuild:

```css
@theme {
  --color-primary: #1a3a5c;   /* example: change to navy blue */
  --color-accent:  #e87722;   /* example: change to orange */
}
```

No other files need to change. Tailwind regenerates all utilities referencing these tokens.

---

## Contact form backends

Both backends share an identical HTTP contract:

- **Method**: `POST`
- **Body**: `application/x-www-form-urlencoded` with fields `name`, `email`, `message`
- **200**: success (empty body)
- **400**: validation failure (empty body)
- **500**: email send failure (empty body)

The email is sent via the **Resend API**. Both workers require a `RESEND_API_KEY` environment variable / secret.

### Netlify Functions

File: `functions/netlify/contact.js`

Deploy by placing `contact.js` and `netlify.toml` at the root of your Netlify site, or in a directory configured as the functions directory. Set `RESEND_API_KEY` in Netlify's environment variable settings. The function is available at `/.netlify/functions/contact`.

### Cloudflare Workers

File: `functions/cloudflare/worker.js` + `wrangler.toml`

Deploy with `wrangler deploy` from the `functions/cloudflare/` directory. Add `RESEND_API_KEY` with `wrangler secret put RESEND_API_KEY`. Point `form_endpoint` in `config.yml` to the Worker URL.

The Cloudflare Worker uses `request.formData()` (native Web API) instead of manual URL parsing, which is the main implementation difference from the Netlify version.

---

## Tailwind binary

The build uses the **Tailwind CSS v4 standalone CLI** — a single self-contained binary. No Node.js, no npm, no `node_modules`.

The binary is pinned to `v4.0.4` in `build.sh` and `build.bat`. To upgrade:
1. Change `tailwind_version` in the build script
2. Delete `bin/tailwindcss` (or `bin/tailwindcss.exe` on Windows)
3. Run the build script — it re-downloads automatically

The binary is placed at `bin/tailwindcss` (Linux/macOS) or `bin/tailwindcss.exe` (Windows) and is `.gitignore`d.

---

## SEO features

- `<meta name="description">` — auto-generated from first paragraph of each Markdown page
- Open Graph `og:title`, `og:description`, `og:url`, `og:image` — on every page
- `og:image` uses the page-specific image slot if present, falls back to `about-1`, omits the tag if no images exist
- `sitemap.xml` — lists all enabled pages with `<lastmod>` set to today's build date
- `robots.txt` — `Allow: /` for all bots, sitemap pointer

---

## Frontend libraries (CDN, no build step)

| Library | Version | Purpose |
|---|---|---|
| HTMX | 2.0.3 | Contact form async POST (no page reload) |
| Alpine.js | 3.14.1 | Mobile navigation open/close toggle |

Both are loaded from CDN in `_base.html`. HTMX uses a SRI hash (`integrity=`). Alpine.js is deferred.

---

## Python dependencies

```
Jinja2==3.1.4    — HTML template engine
PyYAML==6.0.1    — parses config.yml and content YAML files
Markdown==3.6    — converts .md files to HTML
```

All three are pure Python. No C extensions required. Install with:
```bash
pip install -r requirements.txt
```

---

## `output/` structure

```
output/
├── index.html                     # Home page
├── tietoa-jarjestosta/index.html  # About page (if enabled)
├── toiminta/index.html            # Activities page (if enabled)
├── tapahtumat/index.html          # Events page (if enabled)
├── yhteystiedot/index.html        # Contact page
├── 404.html                       # Not-found page
├── sitemap.xml
├── robots.txt
└── static/
    ├── css/
    │   └── main.css               # Compiled + minified Tailwind CSS
    ├── images/
    │   └── *.jpg / *.png / favicon.svg
    └── fonts/
        └── *.woff2
```

All HTML files use root-relative paths (`/static/css/main.css`) so the site can be served from the root of any domain without path adjustment.

---

## Common tasks cheat sheet

| Task | What to change |
|---|---|
| Change body text on a page | Edit the `.md` file in `content/` |
| Add or remove an event | Edit `content/tapahtumat.yml` |
| Change contact details | Edit `content/yhteystiedot.yml` |
| Enable / disable a page | `pages.<key>: true/false` in `config.yml` |
| Add a social link | `social.<platform>: "url"` in `config.yml` |
| Change brand colours | Edit hex values in `src/input.css` `@theme` block |
| Add a page image | Drop `<slot>.jpg` into `images/` |
| Enable contact form | Deploy a backend, set `form_endpoint` in `config.yml` |
| Change site URL (for sitemap/OG) | `site.url` in `config.yml` |
| Upgrade Tailwind | Update version in `build.sh`/`build.bat`, delete `bin/tailwindcss` |
