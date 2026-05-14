# cli.py

from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from scope import build_scope, describe_scope
from discovery.passive import PassiveDiscovery
from crawler.engine import CrawlEngine
from graph import AttackSurfaceGraph
from models import Node, NodeType
from fingerprint import FingerprintEngine
from risk import apply_risk

from exporters.markdown_export import export_markdown
from exporters.json_export import export_json
from exporters.html_export import export_html
from exporters.csv_export import export_endpoints_csv
from exporters.neo4j_export import export_neo4j

from dorks import build_dorks
from probe import probe_hosts


console = Console()

BANNER = r"""
 ███████╗██╗   ██╗██████╗ ████████╗██████╗  █████╗  ██████╗███████╗
 ██╔════╝██║   ██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
 ███████╗██║   ██║██████╔╝   ██║   ██████╔╝███████║██║     █████╗
 ╚════██║██║   ██║██╔══██╗   ██║   ██╔══██╗██╔══██║██║     ██╔══╝
 ███████║╚██████╔╝██████╔╝   ██║   ██║  ██║██║  ██║╚██████╗███████╗
 ╚══════╝ ╚═════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
"""


def show_banner():
    console.clear()
    console.print(
        Panel.fit(
            Text(BANNER, style="bold green"),
            border_style="green",
            title="Subtrace v2",
        )
    )


def _target_to_seed_url(target: str) -> str:
    if "://" not in target:
        return f"https://{target}"
    return target


def _target_to_domain(target: str) -> str:
    if "://" not in target:
        return target
    return urlparse(target).netloc


def _host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


class AppState:
    def __init__(self):
        self.target: str | None = None
        self.scope = None
        self.graph: AttackSurfaceGraph | None = None

        self.passive_result: dict | None = None
        self.probe_result: list[dict] | None = None

        self.crawl_result: dict | None = None
        self.tech: list[str] = []
        self.dorks: list[dict] = []


def build_menu(target: str | None):
    table = Table(title="Attack Surface Mapper")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Action", style="green")

    table.add_row("T", f"Set Target (current: {target or 'NOT SET'})")
    table.add_row("1", "Passive Discovery (+DNS + reachability probe)")
    table.add_row("2", "Live Crawling")
    table.add_row("3", "Playwright SPA Scan (browser rendering)")
    table.add_row("4", "Historical URL Analysis (from passive)")
    table.add_row("5", "Technology Fingerprinting")
    table.add_row("6", "Risk Analysis")
    table.add_row("7", "Run Full Pipeline")
    table.add_row("8", "Export Reports")
    table.add_row("D", "Google Dorks (generate links)")
    table.add_row("9", "Show Graph Stats (JSON)")
    table.add_row("0", "Exit")

    console.print(table)


async def action_passive(state: AppState):
    if not state.target:
        console.print("[red]No target set. Press T first.[/red]")
        return

    domain = _target_to_domain(state.target)
    state.scope = build_scope([domain])

    console.print("[cyan]Running passive discovery...[/cyan]")
    console.print(describe_scope(state.scope))

    with console.status(
        "[bold green]Querying crt.sh, OTX, HackerTarget, Wayback...[/bold green]"
    ):
        pd = PassiveDiscovery()
        try:
            result = await pd.enumerate(domain)
        finally:
            await pd.close()

    state.passive_result = result

    # dorks are deterministic (no network)
    state.dorks = build_dorks(domain)

    subs = result.get("subdomains", []) or []

    with console.status("[bold green]Probing subdomains over HTTP/HTTPS...[/bold green]"):
        probes = await probe_hosts(subs, concurrency=60, timeout=10)

    state.probe_result = probes

    resolved_index = {r.get("hostname"): r for r in (result.get("resolved", []) or []) if r.get("hostname")}

    probe_by_host: dict[str, list[dict]] = {}
    for p in probes:
        host = _host_from_url(p.get("url", ""))
        if not host:
            continue
        probe_by_host.setdefault(host, []).append(p)

    graph = state.graph or AttackSurfaceGraph()
    graph.add_node(Node(type=NodeType.DOMAIN, value=domain, label=domain))

    # subdomains with DNS + probe metadata
    for sub in subs:
        meta = {
            "origin": "passive",
            "dns": resolved_index.get(sub, {}),
            "probe": probe_by_host.get(sub, []),
        }
        graph.add_node(Node(type=NodeType.SUBDOMAIN, value=sub, label=sub, metadata=meta))

    # historical urls as URL nodes (wayback)
    for u in result.get("historical_urls", []) or []:
        graph.add_node(
            Node(type=NodeType.URL, value=u, label=u, metadata={"origin": "wayback"})
        )

    state.graph = graph

    reachable_hosts = 0
    for sub in subs:
        if any(x.get("ok") for x in probe_by_host.get(sub, [])):
            reachable_hosts += 1

    console.print(
        f"[green]Passive done.[/green] Subdomains: {len(subs)} "
        f"(reachable: {reachable_hosts}), URLs: {len(result.get('historical_urls', []) or [])}"
    )


async def action_crawl(state: AppState, use_browser: bool = False):
    if not state.target:
        console.print("[red]No target set. Press T first.[/red]")
        return

    domain = _target_to_domain(state.target)
    seed = _target_to_seed_url(state.target)
    state.scope = state.scope or build_scope([domain])

    console.print("[cyan]Starting crawler...[/cyan]")
    console.print(describe_scope(state.scope))

    latest = {
        "visited": 0,
        "discovered": 0,
        "current_url": "",
        "queue_size": 0,
        "depth": 0,
        "results": 0,
        "max_pages": 0,
    }

    def on_update(info: dict):
        latest.update(info)

    engine = CrawlEngine(
        scope=state.scope,
        concurrency=10,
        max_depth=2,
        max_pages=300,
        use_browser=use_browser,
        on_update=on_update,
        log_every=1,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TextColumn(
            "visited={task.fields[visited]} discovered={task.fields[discovered]} "
            "queue={task.fields[queue]} depth={task.fields[depth]}"
        ),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task(
            "Crawling...",
            total=engine.max_pages,
            visited=0,
            discovered=0,
            queue=0,
            depth=0,
        )

        crawl_task = asyncio.create_task(engine.crawl([seed]))

        while not crawl_task.done():
            progress.update(
                task,
                completed=min(latest.get("visited", 0), engine.max_pages),
                visited=latest.get("visited", 0),
                discovered=latest.get("discovered", 0),
                queue=latest.get("queue_size", 0),
                depth=latest.get("depth", 0),
                description=f"Crawling: {latest.get('current_url','')[:80]}",
            )
            await asyncio.sleep(0.1)

        result = await crawl_task

        progress.update(
            task,
            completed=min(len(result.get("visited", [])), engine.max_pages),
            visited=len(result.get("visited", [])),
            discovered=len(result.get("discovered", [])),
            queue=0,
            depth=latest.get("depth", 0),
            description="Crawling complete",
        )

    state.crawl_result = result

    graph = state.graph or AttackSurfaceGraph()

    # Endpoints (visited)
    for url in result.get("visited", []) or []:
        graph.add_node(
            Node(
                type=NodeType.ENDPOINT,
                value=url,
                label=url,
                metadata={"origin": "crawl", "method": "GET"},
            )
        )

    # Discovered endpoints (JS/sourcemaps/browser requests)
    for url in result.get("discovered", []) or []:
        graph.add_node(
            Node(
                type=NodeType.ENDPOINT,
                value=url,
                label=url,
                metadata={"origin": "discovered", "method": "GET"},
            )
        )

    # Enrich endpoints using crawler response/html records
    response_by_url: dict[str, dict] = {}
    html_by_url: dict[str, dict] = {}

    for item in result.get("results", []) or []:
        t = item.get("type")
        u = item.get("url")
        if not u:
            continue
        if t == "response":
            response_by_url[u] = item.get("data", {}) or {}
        elif t == "html":
            html_by_url[u] = item.get("data", {}) or {}

    for node in graph.nodes_by_type(NodeType.ENDPOINT):
        resp = response_by_url.get(node.value)
        if resp:
            node.metadata.update(resp)

        html = html_by_url.get(node.value)
        if html:
            # keep the parsed html structure; it is useful for reports later
            node.metadata["html"] = html

    state.graph = graph

    console.print(
        f"[green]Crawl done.[/green] Visited: {len(result.get('visited', []) or [])}, "
        f"Discovered: {len(result.get('discovered', []) or [])}"
    )


def action_historical(state: AppState):
    if not state.passive_result:
        console.print("[red]No passive data. Run Passive Discovery first.[/red]")
        return
    urls = state.passive_result.get("historical_urls", []) or []
    console.print(f"[cyan]Historical URLs (Wayback):[/cyan] {len(urls)}")
    for u in urls[:80]:
        console.print(f"- {u}")
    if len(urls) > 80:
        console.print(f"[yellow](showing first 80 of {len(urls)})[/yellow]")


def action_fingerprint(state: AppState):
    if not state.crawl_result or not state.graph:
        console.print("[red]No crawl data/graph. Run Live Crawling first.[/red]")
        return

    fp = FingerprintEngine()

    response_by_url: dict[str, dict] = {}
    html_by_url: dict[str, dict] = {}

    for item in state.crawl_result.get("results", []) or []:
        t = item.get("type")
        url = item.get("url")
        if not url:
            continue
        if t == "response":
            response_by_url[url] = item.get("data", {}) or {}
        elif t == "html":
            html_by_url[url] = item.get("data", {}) or {}

    all_tech = set()

    for node in state.graph.nodes_by_type(NodeType.ENDPOINT):
        headers = (response_by_url.get(node.value, {}).get("headers") or {})

        html_data = html_by_url.get(node.value, {}) or {}
        scripts = html_data.get("scripts", []) if isinstance(html_data, dict) else []
        meta = html_data.get("metadata", {}) if isinstance(html_data, dict) else {}
        generator = meta.get("generator") or ""
        title = meta.get("title") or ""

        # we don't store full html body; fake_html uses strong signals (generator/title/scripts)
        fake_html = f"{generator}\n{title}\n" + "\n".join(scripts)

        techs = fp.analyze(
            headers=headers,
            html=fake_html,
            urls=scripts,
        )["technologies"]

        if techs:
            node.metadata["technologies"] = techs
            all_tech.update(techs)

    state.tech = sorted(all_tech)

    # optional: one technology node as summary
    if state.tech:
        state.graph.add_node(
            Node(
                type=NodeType.TECHNOLOGY,
                value=",".join(state.tech),
                label="Technologies",
                metadata={"technologies": state.tech},
            )
        )

    console.print(
        f"[green]Detected technologies:[/green] {', '.join(state.tech) if state.tech else '(none)'}"
    )


def action_risk(state: AppState):
    if not state.graph:
        console.print("[red]No graph. Run a scan first.[/red]")
        return

    with console.status("[bold green]Scoring endpoints...[/bold green]"):
        apply_risk(state.graph)

    console.print("[green]Risk scoring applied to endpoints.[/green]")


async def action_full_pipeline(state: AppState):
    await action_passive(state)
    await action_crawl(state, use_browser=False)
    action_fingerprint(state)
    action_risk(state)


def action_dorks(state: AppState):
    if not state.target:
        console.print("[red]No target set.[/red]")
        return

    domain = _target_to_domain(state.target)
    dorks = state.dorks or build_dorks(domain)

    console.print(f"\n[bold green]Google dorks for {domain}[/bold green]\n")
    for d in dorks:
        console.print(f"[cyan]{d['name']}[/cyan]")
        console.print(f"  query: {d['query']}")
        console.print(f"  url:   {d['url']}\n")


def export_menu() -> set[str]:
    console.print("\n[bold green]Export Formats[/bold green]")
    console.print("1) Markdown (.md)")
    console.print("2) JSON (.json)")
    console.print("3) HTML (.html)")
    console.print("4) CSV Endpoints (.csv)")
    console.print("5) Neo4j Cypher (.cypher)")
    console.print("A) All")
    console.print("0) Cancel")
    choice = Prompt.ask("Select export", default="A").strip().upper()

    mapping = {
        "1": {"md"},
        "2": {"json"},
        "3": {"html"},
        "4": {"csv"},
        "5": {"neo4j"},
        "A": {"md", "json", "html", "csv", "neo4j"},
        "0": set(),
    }
    return mapping.get(choice, set())


def action_export(state: AppState):
    if not state.graph:
        console.print("[red]No data to export. Run a scan first.[/red]")
        return

    selected = export_menu()
    if not selected:
        console.print("[yellow]Export canceled.[/yellow]")
        return

    if "md" in selected:
        with open("subtrace_report.md", "w", encoding="utf-8") as f:
            f.write(export_markdown(state.graph))
        console.print("[green]Wrote subtrace_report.md[/green]")

    if "json" in selected:
        with open("subtrace_report.json", "w", encoding="utf-8") as f:
            f.write(export_json(state.graph))
        console.print("[green]Wrote subtrace_report.json[/green]")

    if "html" in selected:
        # embed dorks into the graph as a URL node list (so exporter can show them)
        # simplest: create one node holding all dorks in metadata
        if state.dorks:
            state.graph.add_node(Node(
                type=NodeType.URL,
                value="google_dorks",
                label="Google Dorks",
                metadata={"origin": "dorks", "dorks": state.dorks},
            ))

        with open("subtrace_report.html", "w", encoding="utf-8") as f:
            f.write(export_html(state.graph))
        console.print("[green]Wrote subtrace_report.html[/green]")

    if "csv" in selected:
        with open("subtrace_endpoints.csv", "w", encoding="utf-8") as f:
            f.write(export_endpoints_csv(state.graph))
        console.print("[green]Wrote subtrace_endpoints.csv[/green]")

    if "neo4j" in selected:
        with open("subtrace_neo4j.cypher", "w", encoding="utf-8") as f:
            f.write(export_neo4j(state.graph))
        console.print("[green]Wrote subtrace_neo4j.cypher[/green]")


def action_stats(state: AppState):
    if not state.graph:
        console.print("[yellow]No graph yet.[/yellow]")
        return
    console.print(state.graph.to_json(indent=2))


def launch_cli():
    show_banner()
    state = AppState()

    while True:
        build_menu(state.target)
        choice = Prompt.ask("[bold green]Select option[/bold green]").strip().upper()

        if choice == "T":
            t = Prompt.ask(
                "[bold yellow]Target domain or URL[/bold yellow] (e.g. example.com or https://example.com)"
            ).strip()
            if not t:
                console.print("[red]Invalid target.[/red]")
                continue
            state.target = t
            state.scope = None
            console.print(f"[green]Target set:[/green] {state.target}")

        elif choice == "1":
            asyncio.run(action_passive(state))

        elif choice == "2":
            asyncio.run(action_crawl(state, use_browser=False))

        elif choice == "3":
            asyncio.run(action_crawl(state, use_browser=True))

        elif choice == "4":
            action_historical(state)

        elif choice == "5":
            action_fingerprint(state)

        elif choice == "6":
            action_risk(state)

        elif choice == "7":
            asyncio.run(action_full_pipeline(state))

        elif choice == "8":
            action_export(state)

        elif choice == "D":
            action_dorks(state)

        elif choice == "9":
            action_stats(state)

        elif choice == "0":
            break

        else:
            console.print("[red]Invalid selection.[/red]")