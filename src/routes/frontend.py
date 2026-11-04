from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import time

from flask import Blueprint, Response, send_from_directory
import markdown2
import requests

frontend = Blueprint(
    "frontend",
    __name__,
    static_folder=Path(os.path.abspath(__file__)).parent.parent.joinpath("frontend"),
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://eteavfeiumodbjywzqfa.supabase.co")
SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0ZWF2ZmVpdW1vZGJqeXd6cWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NTY1MDIsImV4cCI6MjA3MDUzMjUwMn0.OoB4llKDEtXq0CGgPavqMYEAsZtRF8St_C-YPU-MNPw",
)

FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 512'>"
    "<path fill='#00f5ff' d='M392.8 1.2c-17-4.9-34.7 5-39.6 22l-128 448c-4.9 17 5 34.7 22 39.6s34.7-5 39.6-22l128-448c4.9-17-5-34.7-22-39.6zm80.6 120.1c-12.5 12.5-12.5 32.8 0 45.3L562.7 256l-89.4 89.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l112-112c12.5-12.5 12.5-32.8 0-45.3l-112-112c-12.5-12.5-32.8-12.5-45.3 0zm-306.7 0c-12.5-12.5-32.8-12.5-45.3 0l-112 112c-12.5 12.5-12.5 32.8 0 45.3l112 112c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256l89.4-89.4c12.5-12.5 12.5-32.8 0-45.3z'/>"
    "</svg>"
)

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /create_blog_post
Disallow: /send_email
Disallow: /add_email
Disallow: /remove_email/

Sitemap: https://shaymanor.com/sitemap.xml
"""

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://shaymanor.com/</loc>
    <lastmod>2026-11-04</lastmod>
  </url>
  <url>
    <loc>https://shaymanor.com/projects</loc>
    <lastmod>2026-11-04</lastmod>
  </url>
  <url>
    <loc>https://shaymanor.com/resume</loc>
    <lastmod>2026-11-04</lastmod>
  </url>
  <url>
    <loc>https://shaymanor.com/blog</loc>
    <lastmod>2026-11-04</lastmod>
  </url>
</urlset>
"""

_blog_cache = {"html": None, "expires_at": 0.0}
_BLOG_CACHE_TTL = 300.0


def _format_blog_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        return f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    except Exception:
        return html.escape(str(date_str))


def _render_post_article(post: dict) -> str:
    title = html.escape(str(post.get("title") or "Untitled"))
    date_formatted = _format_blog_date(post.get("created_at") or "")
    tldr_raw = str(post.get("tldr") or "")
    tldr_html = ""
    if tldr_raw:
        has_prefix = bool(re.match(r"^(tl;dr|tldr)[\s:]", tldr_raw.strip(), re.IGNORECASE))
        tldr_class = "blog-post-tldr has-tldr" if has_prefix else "blog-post-tldr"
        tldr_html = f'<div class="{tldr_class}">{html.escape(tldr_raw)}</div>'

    body_md = str(post.get("body") or "")
    body_html = markdown2.markdown(
        body_md,
        extras=["fenced-code-blocks", "tables", "strike"],
    )
    return (
        '<article class="blog-post">'
        '<div class="blog-post-header">'
        f'<h2 class="blog-post-title">{title}</h2>'
        f'<div class="blog-post-date">{date_formatted}</div>'
        "</div>"
        f"{tldr_html}"
        f'<div class="blog-post-content">{body_html}</div>'
        "</article>"
    )


def _get_prerendered_blog_html() -> str | None:
    now = time.monotonic()
    if _blog_cache["html"] and now < _blog_cache["expires_at"]:
        return _blog_cache["html"]

    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/site_blog?select=id,title,tldr,body,created_at&order=created_at.desc&limit=20",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
            },
            timeout=4,
        )
        if not resp.ok:
            return _blog_cache["html"]
        posts = resp.json()
        if not isinstance(posts, list) or not posts:
            return _blog_cache["html"]

        template_path = Path(frontend.static_folder) / "blog.html"
        template_html = template_path.read_text(encoding="utf-8")
        posts_html = "\n".join(_render_post_article(p) for p in posts)

        blog_postings = []
        for p in posts[:10]:
            item = {
                "@type": "BlogPosting",
                "headline": str(p.get("title") or "Untitled"),
                "author": {"@id": "https://shaymanor.com/#person"},
            }
            if p.get("created_at"):
                item["datePublished"] = str(p["created_at"])
            if p.get("tldr"):
                item["description"] = str(p["tldr"])
            blog_postings.append(item)

        blog_ld = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "@id": "https://shaymanor.com/blog#blog",
            "url": "https://shaymanor.com/blog",
            "name": "AI, ML & Systems Engineering Blog — Shay Manor",
            "description": "Technical articles and synthesis by Shay Manor covering AI/ML breakthroughs, systems engineering, autonomous robotics, and developer tools.",
            "author": {"@id": "https://shaymanor.com/#person"},
            "publisher": {"@id": "https://shaymanor.com/#person"},
            "blogPost": blog_postings,
        }

        rendered = template_html.replace(
            '<div id="blog-loading" class="loading-container">',
            '<div id="blog-loading" class="loading-container" style="display: none;">',
            1,
        ).replace(
            '<div id="blog-posts" class="blog-posts-container"></div>',
            f'<div id="blog-posts" class="blog-posts-container">{posts_html}</div>',
            1,
        )
        rendered = re.sub(
            r'<script type="application/ld\+json">.*?</script>',
            lambda _m: f'<script type="application/ld+json">\n  {json.dumps(blog_ld, ensure_ascii=False)}\n  </script>',
            rendered,
            count=1,
            flags=re.DOTALL,
        )
        _blog_cache["html"] = rendered
        _blog_cache["expires_at"] = now + _BLOG_CACHE_TTL
        return rendered
    except Exception:
        return _blog_cache["html"]


@frontend.get("/favicon.ico")
def favicon():
    return Response(FAVICON_SVG, mimetype="image/svg+xml")


@frontend.get("/robots.txt")
def robots():
    return Response(ROBOTS_TXT, mimetype="text/plain")


@frontend.get("/sitemap.xml")
def sitemap():
    return Response(SITEMAP_XML, mimetype="application/xml")


@frontend.get("/scripts.js")
def scripts():
    return frontend.send_static_file("scripts.js")


@frontend.get("/styles.css")
def styles():
    return frontend.send_static_file("styles.css")


@frontend.route("/", methods=["GET"])
def root():
    return send_from_directory(frontend.static_folder, "index.html")


@frontend.route("/projects", methods=["GET"])
def projects():
    return send_from_directory(frontend.static_folder, "projects.html")


@frontend.route("/blog", methods=["GET"])
def blog():
    prerendered = _get_prerendered_blog_html()
    if prerendered:
        return Response(prerendered, mimetype="text/html")
    return send_from_directory(frontend.static_folder, "blog.html")


@frontend.route("/resume", methods=["GET"])
def resume():
    return send_from_directory(frontend.static_folder, "resume.html")
