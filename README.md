```markdown
# Subtrace v2 — Attack Surface Mapper

Subtrace is a Python-based attack surface mapping tool that combines:

- Passive discovery (subdomains + historical URLs)
- Live crawling (HTML link extraction + JavaScript endpoint mining + sourcemap hints)
- Technology fingerprinting
- Heuristic risk scoring
- Exportable reports (HTML/Markdown/JSON/CSV + Neo4j Cypher)

This repository currently uses a **flat module layout** (files at repo root such as `cli.py`, `graph.py`, etc.). It is designed to run locally from the project directory.

---

## Features

### Discovery
- **Passive subdomain enumeration**:
  - `crt.sh` certificate transparency
  - AlienVault OTX passive DNS
  - HackerTarget hostsearch
  - Wayback Machine (domain URL archive)
- **Async DNS resolution** for discovered hosts
- **HTTP/HTTPS probing** to determine which subdomains are reachable and what status/server they return

### Crawling
- Async HTTP crawling with:
  - URL canonicalization (removes tracking params, normalizes query ordering)
  - robots.txt support
  - per-host rate limiting
  - HTML parsing:
    - links
    - scripts
    - forms
    - basic metadata (title, generator)
  - JavaScript analysis:
    - regex-based endpoint detection
    - AST-based route extraction (requires `esprima`)
    - JWT-like token detection (heuristic)
    - websocket URL detection
  - sourcemap analysis (`.map`):
    - source list parsing
    - route-like strings extraction

### Analysis
- **Technology fingerprinting** based on patterns found in:
  - response headers (subset)
  - script URLs
  - HTML metadata signals
- **Risk scoring** for endpoint nodes using path/method heuristics:
  - admin panels
  - upload endpoints
  - debug/internal paths
  - GraphQL endpoints
  - backup/sensitive file extensions
  - state-changing HTTP methods

### Reporting / Exporting
- Export scan output to:
  - HTML report (`subtrace_report.html`)
  - JSON report (`subtrace_report.json`)
  - Markdown report (`subtrace_report.md`)
  - CSV endpoints table (`subtrace_endpoints.csv`)
  - Neo4j Cypher import (`subtrace_neo4j.cypher`)
- HTML report includes:
  - KPI summary
  - risk distribution
  - provenance distribution (crawl vs discovered vs wayback, etc.)
  - technologies summary
  - subdomain DNS + reachability table
  - Google dorks table (generated links)

### Google Dorks (Safe Mode)
Subtrace generates dork queries + links for manual investigation.  
It **does not scrape Google** (scraping violates Google ToS and will get you blocked).

---

## Project Structure (flat layout)

Typical structure:

```
.
├── cli.py
├── main.py
├── graph.py
├── models.py
├── risk.py
├── fingerprint.py
├── scope.py
├── dorks.py                # Google dork generator
├── probe.py                # HTTP/HTTPS subdomain probe
├── storage.py              # optional SQLite storage
├── crawler/
│   ├── __init__.py
│   ├── engine.py
│   ├── canonicalize.py
│   ├── extractor_html.py
│   ├── extractor_js.py
│   ├── extractor_sourcemap.py
│   ├── robots.py
│   └── rate_limit.py
├── discovery/
│   ├── __init__.py
│   ├── passive.py
│   ├── crtsh.py
│   ├── otx.py
│   ├── hackertarget.py
│   ├── wayback.py
│   └── dns_async.py
├── exporters/
│   ├── __init__.py
│   ├── html_export.py
│   ├── markdown_export.py
│   ├── json_export.py
│   ├── csv_export.py
│   └── neo4j_export.py
└── parsers/
    ├── __init__.py
    ├── yaml_loader.py
    ├── swagger.py
    ├── openapi.py
    └── graphql.py
```

> Ensure `__init__.py` exists in `crawler/`, `discovery/`, `exporters/`, `parsers/`, `ui/` (even if empty).

---

## Installation

### 1) Create and activate a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

Your `requirements.txt` may not include every dependency needed by all modules.  
Install these (adjust versions as you prefer):

```bash
pip install -r requirements.txt
pip install aiosqlite esprima
```

If you use Playwright scan (browser rendering):

```bash
pip install playwright
playwright install
```

---

## Running Subtrace

### Start the CLI

```bash
python3 main.py
```

You’ll see a Rich-based menu with options like:
- Set Target
- Passive Discovery (+ DNS + probe)
- Live Crawling
- Technology Fingerprinting
- Risk Analysis
- Full Pipeline
- Export Reports
- Google Dorks

---

## Basic Usage Guide

### 1) Set target
Choose **T** and enter either:
- `example.com`
- `https://example.com`

Subtrace will automatically use `https://<domain>` as the initial crawl seed if you enter a bare domain.

### 2) Run Full Pipeline
Choose **7**:
- Passive discovery
- Probe subdomains
- Crawl target
- Fingerprint technologies
- Apply risk scoring

### 3) Export reports
Choose **8** and select formats:
- Markdown, JSON, HTML, CSV, Neo4j, or All

Outputs are written to the project directory as:
- `subtrace_report.html`
- `subtrace_report.json`
- `subtrace_report.md`
- `subtrace_endpoints.csv`
- `subtrace_neo4j.cypher`

---

## Understanding Output Data

### Provenance / Origins
Subtrace stores where data came from in `node.metadata["origin"]`, such as:
- `passive` (subdomains)
- `crawl` (visited pages)
- `discovered` (endpoints extracted from JS/sourcemaps/browser requests)
- `wayback` (historical URLs)
- `dorks` (generated search queries)

The HTML report shows a distribution of endpoints and URL nodes by origin.

### Subdomain Reachability
During passive discovery, each subdomain is probed over:
- `https://subdomain`
- `http://subdomain`

Results are stored in each SUBDOMAIN node as:

- `metadata["dns"]` -> DNS resolution (A records + CNAME)
- `metadata["probe"]` -> list of probe results (status_code, final_url, server, etc.)

---

## Neo4j Export (how to use it)

The file `subtrace_neo4j.cypher` contains Cypher statements to create nodes/relationships.

### Import via Neo4j Browser
1. Start Neo4j
2. Open Neo4j Browser (typically http://localhost:7474)
3. Paste the cypher file contents into the query pane and run

### Import via cypher-shell
```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p 'yourpassword' < subtrace_neo4j.cypher
```

Example queries:

```cypher
MATCH (n) RETURN labels(n), count(*) ORDER BY count(*) DESC;
```

```cypher
MATCH (e:ENDPOINT)
RETURN e.value, e.risk, e.score
ORDER BY e.score DESC
LIMIT 25;
```

---

## Configuration Notes

### SSL verification
Crawler runs with `verify=False` by default (useful for recon, but can be changed).

### robots.txt
Crawler respects robots.txt by default.  
If you want a switch to disable it, you can add a setting in `crawler/engine.py` and/or `config.py`.

### Crawl limits
Crawler is bounded by:
- `max_depth`
- `max_pages`

These are currently set in `cli.py` when creating `CrawlEngine`.

---

## Troubleshooting

### “No module named X”
- Ensure you are running from the project root
- Ensure you have `__init__.py` in module folders
- Install missing packages (`pip install aiosqlite esprima` etc.)

### Crawl shows visited=0
Common causes:
- robots.txt disallowing crawling
- target requires auth or blocks scanners
- scope filtering excludes host
- network/DNS errors

Try:
- Set target as `http://...` if site doesn’t support HTTPS
- Increase timeouts in crawler
- Temporarily disable robots checks (requires code change)

### Playwright scan fails
- Ensure:
  ```bash
  playwright install
  ```
- On Kali, you may need additional system dependencies for Chromium.

---

## Legal / Ethical Use
Use Subtrace only on targets you own or have explicit authorization to test.  
Passive sources (crt.sh, OTX, etc.) and generated Google dorks should be used responsibly and in compliance with applicable policies/ToS.

---

## Roadmap Ideas
- True concurrent crawl worker pool (concurrency currently reserved but not used)
- Store full endpoint metadata consistently via the `Endpoint` dataclass
- Add sitemap.xml ingestion and robots disallow path collection as endpoints
- Improve JS endpoint discovery + enqueue discovered routes (optional)
- Export to more formats (SARIF, Burp sitemap, etc.)
- Add pluggable risk rules + scoring calibration
- Integrate SQLite storage and session history in CLI

```
