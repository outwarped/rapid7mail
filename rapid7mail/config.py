from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class Config:
    body_keywords: Set[str]
    agent_email: str
    allowed_emails: Set[str]
    max_allowed_output_size: int = 1024 * 1024
    smtpd_hostname: str = "0.0.0.0"
    smtpd_port: int = 8025
    smtp_client_port: int = 8026
    smtp_client_hostname: str = "0.0.0.0"
    python_workers: int = 4
    python_eval_timeout: int = 10
