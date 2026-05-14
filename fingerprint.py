# subtrace/fingerprint.py

from __future__ import annotations

from typing import Dict, List, Set


TECH_SIGNATURES = {
    "react": [
        "react",
        "_reactrootcontainer",
        "__reactfiber",
    ],

    "nextjs": [
        "_next",
        "__next",
    ],

    "vue": [
        "__vue__",
        "vue.js",
    ],

    "angular": [
        "ng-version",
        "angular.js",
    ],

    "graphql": [
        "/graphql",
        "graphql",
    ],

    "apollo": [
        "apolloclient",
        "x-apollo",
    ],

    "aws": [
        "amazonaws.com",
        "cloudfront.net",
    ],

    "cloudflare": [
        "cloudflare",
        "__cf_bm",
        "cf-ray",
    ],

    "stripe": [
        "stripe",
        "js.stripe.com",
    ],

    "firebase": [
        "firebase",
        "firestore",
    ],

    "wordpress": [
        "wp-content",
        "wp-includes",
        "wp-admin",
        "wp-json",
        "/wp-",
        "wordpress",
        "wp_version",
        "wp.js",
        "wp-embed",
    ],

    "woocommerce": [
        "woocommerce",
    ],

    "php": [
        "php",
        "x-powered-by: php",
    ],
}


class FingerprintEngine:

    def __init__(self):
        self.signatures = TECH_SIGNATURES

    def fingerprint_headers(
        self,
        headers: Dict[str, str],
    ) -> Set[str]:
        found = set()

        values = " ".join([
            f"{k} {v}"
            for k, v in headers.items()
        ]).lower()

        for tech, patterns in self.signatures.items():

            for pattern in patterns:

                if pattern.lower() in values:
                    found.add(tech)

        return found

    def fingerprint_html(
        self,
        html: str,
    ) -> Set[str]:
        found = set()

        lower = html.lower()

        for tech, patterns in self.signatures.items():

            for pattern in patterns:

                if pattern.lower() in lower:
                    found.add(tech)

        return found

    def fingerprint_urls(
        self,
        urls: List[str],
    ) -> Set[str]:
        found = set()

        joined = "\n".join(urls).lower()

        for tech, patterns in self.signatures.items():

            for pattern in patterns:

                if pattern.lower() in joined:
                    found.add(tech)

        return found

    def analyze(
        self,
        headers: Dict[str, str],
        html: str,
        urls: List[str],
    ) -> Dict:
        technologies = set()

        technologies.update(
            self.fingerprint_headers(
                headers
            )
        )

        technologies.update(
            self.fingerprint_html(
                html
            )
        )

        technologies.update(
            self.fingerprint_urls(
                urls
            )
        )

        return {
            "technologies": sorted(
                technologies
            ),
            "count": len(
                technologies
            ),
        }
