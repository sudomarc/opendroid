#!/usr/bin/env python3
"""Validate the static website without third-party dependencies."""

from __future__ import annotations

import html.parser
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

HTML_REQUIRED = ("html", "head", "body")
INDEXABLE_PAGES = {
    "index.html", "about.html", "contributor.html", "features.html",
    "privacy.html", "releases.html", "security.html", "support.html", "terms.html",
}
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
CHECKED_NESTING = {
    "html", "head", "body", "main", "header", "footer", "nav", "section",
    "article", "div", "ul", "ol", "li", "button",
}

class PageParser(html.parser.HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack: list[str] = []
        self.counts: dict[str, int] = {}
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.asset_refs: list[tuple[str, str]] = []
        self.scripts: list[tuple[str | None, str]] = []
        self.meta: dict[str, list[str]] = {}
        self.link_rels: dict[str, list[str]] = {}
        self.json_ld: list[str] = []
        self.errors: list[str] = []
        self._json_ld_depth = 0
        self._json_ld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        self.counts[tag] = self.counts.get(tag, 0) + 1
        ident = attrs_dict.get("id")
        if ident:
            if ident in self.ids:
                self.errors.append(f"duplicate id={ident!r}")
            self.ids.add(ident)
        if tag == "meta":
            key = attrs_dict.get("name") or attrs_dict.get("property") or attrs_dict.get("http-equiv")
            if key:
                self.meta.setdefault(key.lower(), []).append(attrs_dict.get("content", ""))
        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if rel:
                for rel_token in rel.split():
                    self.link_rels.setdefault(rel_token, []).append(href)
            if href:
                self.links.append(("link[href]", href))
        if tag in {"a", "area"} and attrs_dict.get("href"):
            self.links.append((f"{tag}[href]", attrs_dict["href"]))
        if tag in {"img", "script", "source", "video", "audio", "iframe", "embed", "object"}:
            attr = "src" if tag != "object" else "data"
            ref = attrs_dict.get(attr, "")
            if ref:
                self.asset_refs.append((f"{tag}[{attr}]", ref))
            if tag == "img" and "alt" not in attrs_dict:
                self.errors.append("img element missing alt attribute")
        if tag in {"video", "audio"} and attrs_dict.get("poster"):
            self.asset_refs.append((f"{tag}[poster]", attrs_dict["poster"]))
        if tag == "script":
            script_type = attrs_dict.get("type") or None
            self.scripts.append((script_type, attrs_dict.get("src", "")))
            if script_type and script_type.lower() == "application/ld+json":
                self._json_ld_depth = 1
                self._json_ld_buffer = []
        if tag in CHECKED_NESTING and tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() in self.stack:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self._json_ld_depth:
            raw = "".join(self._json_ld_buffer).strip()
            if raw:
                self.json_ld.append(raw)
            self._json_ld_depth = 0
            self._json_ld_buffer = []
        if tag not in CHECKED_NESTING:
            return
        if tag not in self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
            return
        if self.stack[-1] != tag:
            self.errors.append(f"misnested closing tag </{tag}>; expected </{self.stack[-1]}>")
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if self._json_ld_depth:
            self._json_ld_buffer.append(data)


def local_target(root: Path, page: Path, ref: str) -> tuple[Path | None, str | None]:
    split = urlsplit(ref)
    if split.scheme or split.netloc:
        return None, None
    path_text = split.path
    fragment = split.fragment or None
    if not path_text:
        return page, fragment
    if path_text.startswith("/"):
        target = root / path_text.lstrip("/")
    else:
        target = page.parent / path_text
    target = target.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None, fragment
    if target.is_dir():
        target = target / "index.html"
    return target, fragment


def validate_css(root: Path) -> list[str]:
    errors: list[str] = []
    for css in root.rglob("*.css"):
        text = css.read_text(encoding="utf-8")
        if text.count("{") != text.count("}"):
            errors.append(f"{css}: CSS brace mismatch")
        for raw in re.findall(r"url\(([^)]+)\)", text, flags=re.I):
            ref = raw.strip().strip("\"'")
            split = urlsplit(ref)
            if not ref or split.scheme or split.netloc or ref.startswith("data:"):
                continue
            target, _ = local_target(root, css, ref)
            if target is not None and not target.exists():
                errors.append(f"{css}: missing CSS asset {ref!r}")
    return errors


def validate_sitemap(root: Path, canonical_origin: str, expected_pages: set[str]) -> list[str]:
    errors: list[str] = []
    sitemap = root / "sitemap.xml"
    if not sitemap.exists():
        return ["missing sitemap.xml"]
    try:
        tree = ET.parse(sitemap)
        root_element = tree.getroot()
    except ET.ParseError as exc:
        return [f"sitemap.xml: invalid XML: {exc}"]
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [el.text.strip() for el in root_element.findall(f"{namespace}url/{namespace}loc") if el.text]
    expected_urls = {
        canonical_origin.rstrip("/") + ("/" if name == "index.html" else f"/{name}")
        for name in expected_pages
    }
    if len(locs) != len(set(locs)):
        errors.append("sitemap.xml: duplicate <loc> entries")
    unexpected = sorted(set(locs) - expected_urls)
    missing = sorted(expected_urls - set(locs))
    if unexpected:
        errors.append("sitemap.xml: unexpected URLs: " + ", ".join(unexpected))
    if missing:
        errors.append("sitemap.xml: missing URLs: " + ", ".join(missing))
    for loc in locs:
        parsed = urlsplit(loc)
        if parsed.scheme != "https" or not loc.startswith(canonical_origin.rstrip("/") + "/"):
            errors.append(f"sitemap.xml: non-canonical URL {loc!r}")
    return errors


def validate_robots(root: Path, sitemap_url: str) -> list[str]:
    robots = root / "robots.txt"
    if not robots.exists():
        return ["missing robots.txt"]
    text = robots.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"^User-agent:\s*\*\s*$", text, flags=re.I | re.M):
        errors.append("robots.txt: missing User-agent: *")
    if not re.search(r"^Allow:\s*/\s*$", text, flags=re.I | re.M):
        errors.append("robots.txt: missing Allow: /")
    matches = re.findall(r"^Sitemap:\s*(\S+)\s*$", text, flags=re.I | re.M)
    if matches != [sitemap_url]:
        errors.append("robots.txt: Sitemap does not match canonical sitemap URL")
    return errors


def validate(root_arg: str) -> int:
    root = Path(root_arg).resolve()
    if not root.is_dir():
        print(f"ERROR: website root does not exist: {root}")
        return 2
    pages = sorted(root.glob("*.html"))
    actual = {p.name for p in pages}
    errors: list[str] = []
    warnings: list[str] = []
    missing_pages = sorted(INDEXABLE_PAGES - actual)
    if missing_pages:
        errors.append(f"missing required pages: {', '.join(missing_pages)}")
    if "404.html" not in actual:
        errors.append("missing required custom 404.html")

    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    canonicals: dict[str, str] = {}
    parsed: dict[Path, PageParser] = {}
    for page in pages:
        parser = PageParser(page)
        try:
            parser.feed(page.read_text(encoding="utf-8"))
            parser.close()
        except Exception as exc:
            errors.append(f"{page}: HTML parser error: {exc}")
            continue
        if parser.stack:
            errors.append(f"{page}: unclosed tags: {', '.join(parser.stack)}")
        parsed[page] = parser
        for required in HTML_REQUIRED:
            if parser.counts.get(required, 0) != 1:
                errors.append(f"{page}: expected exactly one <{required}>")
        if page.name != "404.html" and parser.counts.get("main", 0) != 1:
            if page.name == "index.html" and "main-content" in parser.ids:
                warnings.append(f"{page}: primary content uses <section id=\"main-content\"> instead of a native <main> landmark")
            else:
                errors.append(f"{page}: expected exactly one <main>")
        if parser.counts.get("title", 0) != 1:
            errors.append(f"{page}: expected exactly one <title>")
        title = ""
        raw = page.read_text(encoding="utf-8")
        match = re.search(r"<title>(.*?)</title>", raw, flags=re.I | re.S)
        if match:
            title = re.sub(r"\s+", " ", match.group(1)).strip()
        if page.name in INDEXABLE_PAGES:
            if not title:
                errors.append(f"{page}: empty title")
            elif not 10 <= len(title) <= 70:
                warnings.append(f"{page}: title length is {len(title)} characters")
            titles[page.name] = title
        if not parser.meta.get("viewport", []):
            errors.append(f"{page}: missing viewport meta")
        canonical = parser.link_rels.get("canonical", [])
        if page.name in INDEXABLE_PAGES:
            if len(canonical) != 1:
                errors.append(f"{page}: expected exactly one canonical link")
            else:
                canonical_url = canonical[0]
                canonicals[page.name] = canonical_url
                parsed_canonical = urlsplit(canonical_url)
                if parsed_canonical.scheme != "https" or parsed_canonical.fragment or parsed_canonical.query:
                    errors.append(f"{page}: canonical must be a clean HTTPS URL")
            descriptions_for_page = parser.meta.get("description", [])
            if len(descriptions_for_page) != 1 or not descriptions_for_page[0].strip():
                errors.append(f"{page}: expected one non-empty meta description")
            else:
                desc = re.sub(r"\s+", " ", descriptions_for_page[0]).strip()
                descriptions[page.name] = desc
                if not 50 <= len(desc) <= 170:
                    warnings.append(f"{page}: meta description length is {len(desc)} characters")
            for key, label in {
                "og:title": "title", "og:description": "description", "og:image": "image",
                "og:url": "url", "og:type": "type",
            }.items():
                values = parser.meta.get(key, [])
                if len(values) != 1 or not values[0].strip():
                    errors.append(f"{page}: missing required Open Graph {label}")
        csp_values = parser.meta.get("content-security-policy", [])
        if len(csp_values) != 1:
            errors.append(f"{page}: expected exactly one CSP meta")
        else:
            csp = csp_values[0].lower()
            if "unsafe-eval" in csp:
                errors.append(f"{page}: CSP contains unsafe-eval")
            if re.search(r"(?:^|\s)script-src\s+[^;]*\*", csp):
                errors.append(f"{page}: CSP script-src contains wildcard")
            if re.search(r"(?:^|\s)connect-src\s+[^;]*\*", csp):
                errors.append(f"{page}: CSP connect-src contains wildcard")
            if re.search(r"(?:^|\s)script-src\s+[^;]*unsafe-inline", csp):
                errors.append(f"{page}: CSP script-src contains unsafe-inline")
        for raw_json in parser.json_ld:
            try:
                json.loads(raw_json)
            except json.JSONDecodeError as exc:
                errors.append(f"{page}: invalid JSON-LD: {exc}")
        if page.name in INDEXABLE_PAGES:
            h1_count = len(re.findall(r"<h1\b", raw, flags=re.I))
            if h1_count != 1:
                errors.append(f"{page}: expected exactly one <h1>, found {h1_count}")
            heading_levels = [int(level) for level in re.findall(r"<h([1-6])\b", raw, flags=re.I)]
            for previous, current in zip(heading_levels, heading_levels[1:]):
                if current > previous + 1:
                    errors.append(f"{page}: heading hierarchy skips from h{previous} to h{current}")
                    break
            placeholder_patterns = (
                r"\blorem ipsum\b", r"\bTODO\b", r"\bFIXME\b", r"\bPLACEHOLDER\b",
                r"Your Name Here",
            )
            for pattern in placeholder_patterns:
                if re.search(pattern, raw, flags=re.I):
                    warnings.append(f"{page}: placeholder-like text detected ({pattern}); review before publication")
                    break
        for kind, ref in parser.links + parser.asset_refs:
            target, fragment = local_target(root, page, ref)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{page}: broken {kind} reference {ref!r}")
                continue
            if fragment and target.suffix.lower() == ".html":
                target_parser = parsed.get(target)
                if target_parser is None:
                    target_parser = PageParser(target)
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    target_parser.close()
                if fragment not in target_parser.ids:
                    errors.append(f"{page}: missing fragment {ref!r}")

    if len(set(titles.values())) != len(titles):
        duplicates = sorted(name for name, title in titles.items() if list(titles.values()).count(title) > 1)
        errors.append("duplicate page titles: " + ", ".join(duplicates))
    if len(set(descriptions.values())) != len(descriptions):
        duplicates = sorted(name for name, desc in descriptions.items() if list(descriptions.values()).count(desc) > 1)
        errors.append("duplicate meta descriptions: " + ", ".join(duplicates))

    expected_origin = "https://yashab-cyber.github.io/opendroid"
    expected_canonicals = {
        "index.html": expected_origin + "/",
        **{name: expected_origin + "/" + name for name in INDEXABLE_PAGES if name != "index.html"},
    }
    for page, expected_url in expected_canonicals.items():
        actual_url = canonicals.get(page)
        if actual_url and actual_url != expected_url:
            errors.append(f"{page}: canonical {actual_url!r} does not match expected URL {expected_url!r}")

    errors.extend(validate_css(root))
    errors.extend(validate_sitemap(root, expected_origin, INDEXABLE_PAGES))
    errors.extend(validate_robots(root, expected_origin + "/sitemap.xml"))
    source_maps = list(root.rglob("*.map"))
    if source_maps:
        errors.append("production source maps present: " + ", ".join(str(p.relative_to(root)) for p in source_maps))
    if errors:
        print("WEBSITE VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("WARNINGS:")
            for warning in warnings:
                print(f"- {warning}")
        return 1
    print(f"WEBSITE VALIDATION PASSED: {len(pages)} HTML pages, local links/assets/CSP/metadata/JSON-LD/sitemap checked")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0

if __name__ == "__main__":
    sys.exit(validate(sys.argv[1] if len(sys.argv) > 1 else "website"))
