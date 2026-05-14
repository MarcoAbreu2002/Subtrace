# subtrace/risk.py

from __future__ import annotations

import re

from models import RiskLevel, Endpoint, AssetCategory


# High-signal patterns (attack surface heuristics)
ADMIN_PATTERNS = re.compile(r"/admin|/dashboard|/manage|/console|/backoffice", re.I)
UPLOAD_PATTERNS = re.compile(r"/upload|/file|/media|/avatar|/image", re.I)
AUTH_PATTERNS   = re.compile(r"/login|/auth|/oauth|/token|/register", re.I)
DEBUG_PATTERNS  = re.compile(r"/debug|/test|/staging|/dev|/internal", re.I)
GRAPHQL_PATTERNS = re.compile(r"/graphql", re.I)
BACKUP_FILES = re.compile(r"\.bak$|\.old$|\.backup$|\.env$|\.sql$", re.I)


def score_endpoint(endpoint: Endpoint) -> tuple[float, RiskLevel, list[str]]:
    """
    Returns:
        score (0–100),
        risk level,
        reasoning tags
    """

    score = 0
    reasons = []

    url = endpoint.url.lower()

    # ── AUTH SIGNALS ─────────────────────────────────────────────
    if not endpoint.auth_required:
        score += 15
        reasons.append("no_auth_detected")

    if endpoint.auth_type.value in ("none", "unknown"):
        score += 5
        reasons.append("weak_auth_signal")

    # ── HIGH-RISK PATHS ──────────────────────────────────────────
    if ADMIN_PATTERNS.search(url):
        score += 40
        reasons.append("admin_surface")

    if UPLOAD_PATTERNS.search(url):
        score += 30
        reasons.append("upload_surface")

    if DEBUG_PATTERNS.search(url):
        score += 35
        reasons.append("debug_or_internal")

    if GRAPHQL_PATTERNS.search(url):
        score += 20
        reasons.append("graphql_endpoint")

    if BACKUP_FILES.search(url):
        score += 50
        reasons.append("sensitive_file_exposure")

    # ── CATEGORY BOOSTING ────────────────────────────────────────
    if endpoint.category == AssetCategory.API:
        score += 10
        reasons.append("api_surface")

    if endpoint.category == AssetCategory.PAYMENT:
        score += 25
        reasons.append("payment_surface")

    if endpoint.category == AssetCategory.ADMIN:
        score += 30
        reasons.append("admin_category")

    # ── METHOD RISK ──────────────────────────────────────────────
    if endpoint.method in ("POST", "PUT", "PATCH"):
        score += 5
        reasons.append("state_changing_method")

    # ── FINAL NORMALIZATION ──────────────────────────────────────
    score = min(100, score)

    if score >= 80:
        risk = RiskLevel.CRITICAL
    elif score >= 55:
        risk = RiskLevel.HIGH
    elif score >= 30:
        risk = RiskLevel.MEDIUM
    else:
        risk = RiskLevel.LOW

    return score, risk, reasons


def apply_risk(graph) -> None:
    """
    Mutates graph nodes in-place.
    """

    for node in graph.all_nodes():

        if not node.metadata:
            continue

        # Only score endpoints
        if node.type.value != "endpoint":
            continue

        ep_data = Endpoint(**node.metadata)

        score, risk, reasons = score_endpoint(ep_data)

        node.score = score
        node.risk = risk

        node.metadata["risk_reasons"] = reasons
