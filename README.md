# configurable_static_site

A Python-based static site generator for a Finnish association website (Tusmo ry). One build command reads content files, compiles CSS, renders HTML pages, and writes a self-contained `output/` folder ready to deploy anywhere.

---

## What it does

- Reads content from Markdown files and YAML data files
- Renders pages using Jinja2 HTML templates
- Compiles Tailwind CSS v4 (standalone binary — no Node.js or npm needed)
- Copies images and fonts into the output
- Generates `sitemap.xml` and `robots.txt` automatically
- Enables or disables whole pages from a single `config.yml` toggle

### Pages

| Page | URL | Always on? |
|---|---|---|
| Home | `/` | Yes |
| About the org | `/tietoa-jarjestosta/` | Toggleable |
| Activities | `/toiminta/` | Toggleable |
| Events | `/tapahtumat/` | Toggleable |
| Contact | `/yhteystiedot/` | Yes |
| 404 | `404.html` | Yes |

---

## Requirements

- Python 3.8+
- pip packages: `Jinja2`, `PyYAML`, `Markdown` (see `requirements.txt`)
- Internet access on first build (to auto-download the Tailwind binary)

---

## Quick start

```bash
cd app/

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Build the site (Linux / macOS)
./build.sh

# Build the site (Windows)
build.bat
```

The build script checks for Python, the pip packages, and the Tailwind binary. It downloads the Tailwind binary automatically if it is missing. Output lands in `app/output/`.

**Preview locally:**
```bash
python3 -m http.server 8000 --directory output/
# Open http://localhost:8000
```

---

## Project layout

```
app/
├── build.py              # Main build script (Python)
├── build.sh              # Build runner for Linux / macOS
├── build.bat             # Build runner for Windows
├── config.yml            # Site-wide settings (URL, page toggles, social links)
├── requirements.txt      # Python dependencies
│
├── content/
│   ├── etusivu.md        # Home page body text (Markdown)
│   ├── tietoa-jarjestosta.md  # About page body text (Markdown)
│   ├── toiminta.md       # Activities page body text (Markdown)
│   ├── tapahtumat.yml    # Events list (YAML)
│   └── yhteystiedot.yml  # Organisation contact details (YAML)
│
├── templates/
│   ├── _base.html        # Shared layout: nav, footer, Alpine.js, HTMX
│   ├── home.html         # Home page template
│   ├── about.html        # About page template
│   ├── toiminta.html     # Activities page template
│   ├── tapahtumat.html   # Events page template
│   ├── yhteystiedot.html # Contact page template (includes contact form)
│   ├── 404.html          # Not-found page template
│   └── _partials/
│       ├── form-success.html
│       └── form-error.html
│
├── src/
│   └── input.css         # Tailwind source — brand colours, fonts, custom classes
│
├── images/               # Source images (named slots, see below)
├── fonts/                # Self-hosted .woff2 font files
├── bin/                  # Tailwind binary lives here after first build
│
├── functions/
│   ├── netlify/
│   │   ├── contact.js    # Netlify Function: contact form email handler
│   │   └── netlify.toml  # Netlify config
│   └── cloudflare/
│       ├── worker.js     # Cloudflare Worker: contact form email handler
│       └── wrangler.toml # Cloudflare Wrangler config
│
└── output/               # Generated site (git-ignored) — deploy this folder
```

---

## Configuration

Edit `config.yml` to control the whole site:

```yaml
site:
  url: "https://yoursite.fi"   # Used in sitemap.xml and Open Graph tags

pages:
  about: true       # Set false to remove the page and hide it from nav
  toiminta: true
  tapahtumat: true

sections:
  image_row: true   # Second image block on the home page

social:
  facebook: ""      # Leave blank to hide; add a URL to show in footer
  instagram: ""
  youtube: ""
  twitter: ""
  tiktok: ""

form_endpoint: ""   # URL of your deployed contact form backend
```

---

## Adding content

**Prose pages** — edit the Markdown file for that page:

- Home: `content/etusivu.md`
- About: `content/tietoa-jarjestosta.md`
- Activities: `content/toiminta.md`

Standard Markdown works: headings, bold, italic, lists, links. The first paragraph is used automatically as the page meta description (capped at 160 characters).

**Events** — edit `content/tapahtumat.yml`:

```yaml
events:
  - name: "Event name"
    date: "1.8.2025"
    description: "Optional description."
    location: "Leisikuja 7A, Vantaa"
```

All fields except `name` are optional. Remove or leave blank to hide them.

**Contact details** — edit `content/yhteystiedot.yml`:

```yaml
name: "Your Organisation"
mission: "Short mission statement."
address: "Street, City"
phone: "050 1234567"
email: "info@example.fi"
```

These appear on both the Contact page and in the footer.

---

## Images

Drop images into `app/images/` using these exact names. The build detects their presence and enables/disables the corresponding section automatically.

| File | Used on |
|---|---|
| `home-1.jpg` | Home hero background |
| `home-2.jpg` | Home secondary image (needs `sections.image_row: true`) |
| `about-1.jpg` | About page banner |
| `about-2.jpg` | About page secondary image |
| `toiminta-1.jpg` | Activities page banner |
| `toiminta-2.jpg` | Activities page secondary image |
| `tapahtumat-1.jpg` | Events page banner |
| `yhteystiedot-1.jpg` | (OG image fallback for contact page) |
| `favicon.svg` | Browser tab icon |

Both `.jpg` and `.png` are accepted. If an image file is absent, that section simply does not render — no broken images.

---

## Contact form

The contact form on the Contact page uses HTMX to POST without a page reload. Two serverless backends are provided (pick one):

**Netlify Functions** — copy `functions/netlify/contact.js` and `netlify.toml` to your Netlify site, set the `RESEND_API_KEY` environment variable, then set `form_endpoint` in `config.yml` to `/.netlify/functions/contact`.

**Cloudflare Workers** — deploy `functions/cloudflare/worker.js` with Wrangler, add `RESEND_API_KEY` as a secret, then point `form_endpoint` to your Worker URL.

Both backends validate all three fields (name, email, message) and call the Resend API to deliver the email.

If `form_endpoint` is empty the submit button is disabled with an explanatory tooltip.

---

## Deployment

The `output/` folder is a plain static site. Upload it to any host:

- **Netlify** — drag and drop `output/` or connect via Git with publish directory set to `app/output`
- **Cloudflare Pages** — same approach; build command `./build.sh`, output `app/output`
- **GitHub Pages** — push `output/` contents to the `gh-pages` branch
- Any web server or object storage that serves static files

---

## Customising the look

Brand colours and fonts are defined in `src/input.css` under `@theme`. Change the hex values and rebuild — the entire site updates.

```css
@theme {
  --color-primary: #0f4c4c;   /* navbar, dark sections */
  --color-accent:  #c9a84c;   /* buttons, active nav, badges */
  /* ... */
}
```
