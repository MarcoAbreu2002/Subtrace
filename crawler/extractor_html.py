# subtrace/crawler/extractor_html.py

from __future__ import annotations

from typing import Dict, List

from bs4 import BeautifulSoup

from urllib.parse import urljoin


def extract_links(
    soup: BeautifulSoup,
    base_url: str,
) -> List[str]:
    links = []

    for tag in soup.find_all(
        ["a", "link"],
        href=True,
    ):
        href = tag.get("href")

        if not href:
            continue

        if href.startswith(
            (
                "#",
                "javascript:",
                "mailto:",
                "tel:",
            )
        ):
            continue

        links.append(
            urljoin(base_url, href)
        )

    return links


def extract_scripts(
    soup: BeautifulSoup,
    base_url: str,
) -> List[str]:
    scripts = []

    for script in soup.find_all("script"):

        src = script.get("src")

        if src:
            scripts.append(
                urljoin(base_url, src)
            )

    return scripts


def extract_forms(
    soup: BeautifulSoup,
) -> List[Dict]:
    forms = []

    for form in soup.find_all("form"):

        fields = []

        for field in form.find_all(
            [
                "input",
                "textarea",
                "select",
            ]
        ):
            name = field.get("name")

            if not name:
                continue

            fields.append({
                "name": name,
                "type": field.get(
                    "type",
                    "text",
                ),
                "required": field.has_attr(
                    "required"
                ),
            })

        forms.append({
            "action": form.get(
                "action",
                "",
            ),
            "method": form.get(
                "method",
                "GET",
            ).upper(),
            "fields": fields,
        })

    return forms


def extract_metadata(
    soup: BeautifulSoup,
) -> Dict:
    metadata = {
        "title": None,
        "generator": None,
    }

    title = soup.find("title")

    if title:
        metadata["title"] = title.text.strip()

    generator = soup.find(
        "meta",
        attrs={"name": "generator"},
    )

    if generator:
        metadata["generator"] = generator.get(
            "content"
        )

    return metadata


def parse_html(
    html: str,
    base_url: str,
):
    soup = BeautifulSoup(
        html,
        "lxml",
    )

    return {
        "links": extract_links(
            soup,
            base_url,
        ),
        "scripts": extract_scripts(
            soup,
            base_url,
        ),
        "forms": extract_forms(
            soup,
        ),
        "metadata": extract_metadata(
            soup,
        ),
    }
