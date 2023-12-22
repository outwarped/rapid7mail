from dataclasses import dataclass, field
from typing import Set, Iterable

@dataclass
class Config:
    body_keywords: Set[str] = field(default_factory=set)
    agent_email: str = "agent@rapid7.com"
    allowed_emails: Set[str] = field(default_factory=set)