"""Read public source pages and check recorded excerpts without changing reviews."""
import hashlib
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        elif tag in ("p", "div", "li", "h1", "h2", "h3", "tr", "td", "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()


def capture(url):
    """Caller must validate the source allowlist before using this network helper."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 SG-Navi-source-review/1.0"})
    with urlopen(request, timeout=20) as response:
        body = response.read()
        status, final_url = response.status, response.url
    parser = VisibleText()
    parser.feed(body.decode("utf-8", errors="replace"))
    text = "\n".join(filter(None, (normalize_space(line) for line in "".join(parser.parts).splitlines())))
    return {
        "url": final_url, "http_status": status, "text": text,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
