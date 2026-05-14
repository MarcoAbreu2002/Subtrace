# subtrace/config.py

from dataclasses import dataclass, field
from typing import List, Set


DEFAULT_USER_AGENT = (
    "Subtrace/2.0 (+https://github.com/yourname/subtrace)"
)


TRACKING_PARAMS: Set[str] = {
    "utm_source",
    "utm_campaign",
    "utm_medium",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}


SKIP_EXTENSIONS: Set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mp3",
    ".zip",
    ".gz",
    ".tar",
    ".7z",
}


INTERESTING_EXTENSIONS: Set[str] = {
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".js",
    ".map",
    ".graphql",
    ".gql",
    ".wsdl",
    ".wadl",
}


@dataclass
class ScanConfig:
    max_depth: int = 3
    max_pages: int = 500

    crawl_concurrency: int = 20
    dns_concurrency: int = 100

    request_timeout: int = 15
    connect_timeout: int = 8

    follow_redirects: bool = True
    verify_ssl: bool = False

    enable_playwright: bool = True
    enable_robots: bool = True
    enable_wayback: bool = True
    enable_js_analysis: bool = True
    enable_sourcemaps: bool = True

    rate_limit_per_host: float = 0.5

    user_agent: str = DEFAULT_USER_AGENT

    blocked_hosts: List[str] = field(default_factory=lambda: [
        "googleapis.com",
        "gstatic.com",
        "facebook.com",
        "twitter.com",
        "doubleclick.net",
    ])
