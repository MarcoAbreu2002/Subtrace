# subtrace/models.py

from __future__ import annotations

import uuid

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class NodeType(Enum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP = "ip"

    URL = "url"
    ENDPOINT = "endpoint"
    PARAMETER = "parameter"

    SERVICE = "service"
    API = "api"

    SCRIPT = "script"
    SOURCE_MAP = "source_map"

    AUTH = "auth"
    TECHNOLOGY = "technology"

    STORAGE = "storage"
    BUCKET = "bucket"

    FILE = "file"


class EdgeType(Enum):
    RESOLVES_TO = "resolves_to"
    HOSTS = "hosts"

    LINKS_TO = "links_to"
    CALLS = "calls"

    USES_AUTH = "uses_auth"

    CONTAINS = "contains"

    EXPOSES = "exposes"

    SERVES = "serves"

    DISCOVERED_VIA = "discovered_via"


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuthType(Enum):
    NONE = "none"
    COOKIE = "cookie"
    JWT = "jwt"
    OAUTH = "oauth"
    APIKEY = "api_key"
    BASIC = "basic"
    UNKNOWN = "unknown"


@dataclass
class Node:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])

    type: NodeType = NodeType.URL

    value: str = ""
    label: str = ""

    confidence: float = 1.0

    risk: RiskLevel = RiskLevel.INFO
    score: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    tags: List[str] = field(default_factory=list)

    discovered_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "value": self.value,
            "label": self.label,
            "confidence": self.confidence,
            "risk": self.risk.value,
            "score": self.score,
            "metadata": self.metadata,
            "tags": self.tags,
            "discovered_at": self.discovered_at,
        }


@dataclass
class Edge:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])

    source: str = ""
    target: str = ""

    type: EdgeType = EdgeType.LINKS_TO

    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class Endpoint:
    url: str

    method: str = "GET"

    status_code: int = 0

    content_type: str = ""

    auth_required: bool = False
    auth_type: AuthType = AuthType.UNKNOWN

    parameters: List[Dict[str, Any]] = field(default_factory=list)

    technologies: List[str] = field(default_factory=list)

    scripts: List[str] = field(default_factory=list)

    risk: RiskLevel = RiskLevel.INFO
    score: float = 0.0

    notes: List[str] = field(default_factory=list)

    origin: str = "crawl"

    response_size: int = 0

    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "auth_required": self.auth_required,
            "auth_type": self.auth_type.value,
            "parameters": self.parameters,
            "technologies": self.technologies,
            "scripts": self.scripts,
            "risk": self.risk.value,
            "score": self.score,
            "notes": self.notes,
            "origin": self.origin,
            "response_size": self.response_size,
            "headers": self.headers,
        }


@dataclass
class ScanSession:
    target: str

    started_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    completed_at: str = ""

    endpoints_discovered: int = 0
    assets_discovered: int = 0
    technologies_detected: int = 0

    total_requests: int = 0

    findings: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)
