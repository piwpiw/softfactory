from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for key in ("href", "src"):
            value = attr_map.get(key)
            if value:
                self.links.append(value)


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl deployed web pages and report internal 404 links.")
    parser.add_argument("--base-url", required=True, help="Deployed site base URL, for example https://softfactory-platform.vercel.app")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    base_host = urlparse(base_url).netloc
    start_paths = sorted({"/" + path.relative_to("web").as_posix() for path in Path("web").rglob("*.html")})

    discovered: list[tuple[str, str, str]] = []
    issues: list[tuple[str, str, str, str]] = []

    for path in start_paths:
        page_url = f"{base_url}{path}"
        try:
            html = fetch(page_url)
        except Exception as exc:  # pragma: no cover - network/runtime only
            issues.append((path, path, "SOURCE", str(exc)))
            continue

        parser = LinkParser()
        parser.feed(html)
        for ref in parser.links:
            if not ref or ref.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
                continue
            if "{{" in ref or "}}" in ref or "${" in ref or " " in ref:
                continue
            full = urljoin(page_url, ref)
            parsed = urlparse(full)
            if parsed.netloc != base_host:
                continue
            discovered.append((path, parsed.path or "/", ref))

    checked: set[str] = set()
    for source, target, ref in discovered:
        if target in checked:
            continue
        checked.add(target)
        try:
            html = fetch(f"{base_url}{target}")
            lowered = html[:1200].lower()
            if "<title>404" in lowered or "not found" in lowered[:300]:
                issues.append((source, target, ref, "body-404"))
        except HTTPError as exc:  # pragma: no cover - network/runtime only
            issues.append((source, target, ref, str(exc.code)))
        except URLError as exc:  # pragma: no cover - network/runtime only
            issues.append((source, target, ref, f"urlerr:{exc.reason}"))

    print(f"checked_paths={len(checked)}")
    print(f"issues={len(issues)}")
    for source, target, ref, detail in issues:
        print(f"{source}\t{target}\t{ref}\t{detail}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
