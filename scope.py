# subtrace/scope.py

from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import List
from urllib.parse import urlparse

import tldextract


WILDCARD_RE = re.compile(r"^\*\.[a-zA-Z0-9.-]+$")


@dataclass
class ScopePolicy:
    root_domains: List[str] = field(default_factory=list)

    wildcard_domains: List[str] = field(default_factory=list)

    excluded_domains: List[str] = field(default_factory=list)

    allow_http: bool = True
    allow_https: bool = True

    def normalize_host(self, host: str) -> str:
        return host.lower().strip().strip(".")

    def extract_host(self, value: str) -> str:
        if value.startswith("http://") or value.startswith("https://"):
            return self.normalize_host(urlparse(value).netloc)

        return self.normalize_host(value)

    def is_excluded(self, host: str) -> bool:
        host = self.normalize_host(host)

        for excluded in self.excluded_domains:
            excluded = self.normalize_host(excluded)

            if excluded.startswith("*."):
                base = excluded[2:]

                if host.endswith("." + base):
                    return True

            elif host == excluded:
                return True

        return False

    def is_in_scope(self, host: str) -> bool:
        host = self.extract_host(host)

        if self.is_excluded(host):
            return False

        for root in self.root_domains:
            root = self.normalize_host(root)

            if host == root:
                return True

            if host.endswith("." + root):
                return True

        for wildcard in self.wildcard_domains:
            wildcard = self.normalize_host(wildcard)

            if wildcard.startswith("*."):
                base = wildcard[2:]

                if host.endswith("." + base):
                    return True

        return False

    def is_url_in_scope(self, url: str) -> bool:
        try:
            parsed = urlparse(url)

            if parsed.scheme == "http" and not self.allow_http:
                return False

            if parsed.scheme == "https" and not self.allow_https:
                return False

            return self.is_in_scope(parsed.netloc)

        except Exception:
            return False


def build_scope(
    targets: List[str],
    exclusions: List[str] | None = None,
) -> ScopePolicy:
    exclusions = exclusions or []

    roots = set()
    wildcards = set()

    for target in targets:
        target = target.strip().lower()

        if not target:
            continue

        target = re.sub(r"^https?://", "", target)
        target = target.split("/")[0]

        if WILDCARD_RE.match(target):
            wildcards.add(target)

            base = target[2:]
            roots.add(base)

            continue

        extracted = tldextract.extract(target)

        if extracted.domain and extracted.suffix:
            full = f"{extracted.domain}.{extracted.suffix}"

            if target.startswith(extracted.domain):
                roots.add(target)

            else:
                roots.add(full)

    return ScopePolicy(
        root_domains=sorted(roots),
        wildcard_domains=sorted(wildcards),
        excluded_domains=sorted(set(exclusions)),
    )


def describe_scope(scope: ScopePolicy) -> str:
    lines = []

    lines.append("=== Scope Configuration ===")

    if scope.root_domains:
        lines.append(
            f"Roots: {', '.join(scope.root_domains)}"
        )

    if scope.wildcard_domains:
        lines.append(
            f"Wildcards: {', '.join(scope.wildcard_domains)}"
        )

    if scope.excluded_domains:
        lines.append(
            f"Excluded: {', '.join(scope.excluded_domains)}"
        )

    return "\n".join(lines)
