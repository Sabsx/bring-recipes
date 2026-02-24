#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
from pathlib import Path
from html import escape

# ✅ HIER anpassen:
# Beispiel: https://maxmustermann.github.io/bring-recipes
REPO_PAGES_BASE = "https://Sabsx.github.io/bring-recipes"

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
DOCS_DIR = ROOT / "docs"
ASSETS_IMAGES = "assets/images"

HTML_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="../assets/style.css" />

  <script type="application/ld+json">
{jsonld}
  </script>
</head>
<body>
  <main class="wrap">
    <h1>{title}</h1>
    <div class="sub">{meta}</div>

  <div class="btnrow">
    <a class="btn" href="{bring_link}">🛒 In Bring! importieren</a>
    <a class="btn" href="../">← zurück</a>
  </div>

    {hero_img}

    <section class="grid">
      <article class="card">
        <div class="hd">🧾 Zutaten</div>
        <div class="bd">
          <ul>
{ingredients_html}
          </ul>
        </div>
      </article>

      <article class="card">
        <div class="hd">👨‍🍳 Zubereitung</div>
        <div class="bd">
          <ol>
{instructions_html}
          </ol>
        </div>
      </article>
    </section>

    <footer>
      <a class="btn" href="../">← zurück</a>
    </footer>
  </main>
</body>
</html>
"""

INDEX_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Rezepte</title>
  <link rel="stylesheet" href="./assets/style.css" />
</head>
<body>
  <main class="wrap">
    <h1>Rezepte</h1>
    <div class="sub">Private Rezeptseiten für Bring!-Import</div>

    <section class="card">
      <div class="hd">📚 Liste</div>
      <div class="bd">
        <ul>
{links_html}
        </ul>
      </div>
    </section>

    <footer>
      <span class="muted">Tipp:</span> Öffne ein Rezept und tippe auf <strong>„In Bring! importieren“</strong>.
    </footer>
  </main>
</body>
</html>
"""

def clean_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None and v != ""}

def load_recipes() -> list[dict]:
    out: list[dict] = []
    for p in sorted(RECIPES_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for key in ("slug", "name", "ingredients", "instructions"):
            if key not in data:
                raise ValueError(f"{p}: missing '{key}'")
        out.append(data)
    return out

def build_recipe_page(r: dict) -> None:
    slug = r["slug"]
    title = r["name"]
    desc = f"Privates Rezept: {title}"

    # ✅ Bring Deeplink (öffnet Bring direkt)
    recipe_url = f"{REPO_PAGES_BASE}/{slug}/"
    encoded_url = urllib.parse.quote(recipe_url, safe="")
    bring_link = (
        "https://api.getbring.com/rest/bringrecipes/deeplink"
        f"?url={encoded_url}&source=web"
    )

    # absolute image url for JSON-LD (Bring Bild)
    image_url = None
    if r.get("image_file"):
        image_url = f"{REPO_PAGES_BASE}/{ASSETS_IMAGES}/{r['image_file']}"

    jsonld_obj = clean_none({
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": title,
        "image": image_url if image_url else None,  # string statt array (robuster)
        "recipeYield": r.get("yield"),
        "recipeIngredient": r["ingredients"],
        "recipeInstructions": [{"@type": "HowToStep", "text": t} for t in r["instructions"]],
    })
    jsonld = json.dumps(jsonld_obj, ensure_ascii=False, indent=2)
    jsonld = "\n".join("  " + line for line in jsonld.splitlines())

    ingredients_html = "\n".join(f"            <li>{escape(x)}</li>" for x in r["ingredients"])
    instructions_html = "\n".join(f"            <li>{escape(x)}</li>" for x in r["instructions"])

    meta_parts: list[str] = []
    if r.get("yield"):
        meta_parts.append(f"🍽️ {r['yield']}")
    if r.get("time"):
        meta_parts.append(f"⏱️ {r['time']}")
    meta = " • ".join(meta_parts) if meta_parts else "Bring!-Import kompatibel"

    hero_img = ""
    if r.get("image_file"):
        hero_img = f'<img class="hero" src="../{ASSETS_IMAGES}/{escape(r["image_file"])}" alt="{escape(title)}" />'

    html = HTML_TEMPLATE.format(
        title=escape(title),
        desc=escape(desc),
        meta=escape(meta),
        hero_img=hero_img,
        jsonld=jsonld,
        ingredients_html=ingredients_html,
        instructions_html=instructions_html,
        bring_link=bring_link,
    )

    out_dir = DOCS_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

def build_index(recipes: list[dict]) -> None:
    links = []
    for r in recipes:
        slug = r["slug"]
        name = r["name"]
        links.append(f'          <li><a href="./{escape(slug)}/">{escape(name)}</a></li>')
    links_html = "\n".join(links)

    html = INDEX_TEMPLATE.format(links_html=links_html)
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")

def main() -> None:
    recipes = load_recipes()
    DOCS_DIR.mkdir(exist_ok=True)

    for r in recipes:
        build_recipe_page(r)

    build_index(recipes)
    print(f"Built {len(recipes)} recipes into {DOCS_DIR}")

if __name__ == "__main__":
    main()
