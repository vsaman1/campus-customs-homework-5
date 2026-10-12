from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    BOSS = "boss"
    INVENTORY = "inventory"
    ACCOUNTING = "accounting"
    FACILITIES = "facilities"
    CUSTOMER_SERVICE = "customer_service"


class AuditEntry(BaseModel):
    timestamp: datetime
    agent: AgentRole
    action: str
    task: str = Field(max_length=1_000)
    parent_agent: AgentRole | None = None
    delegation_depth: int = Field(ge=0)
    outcome: str
    tool_name: str | None = None
    tool_arguments: dict[str, object] | None = None


class DelegationRequest(BaseModel):
    target: AgentRole
    task: str = Field(min_length=1, max_length=2_000)


class TicketRunRequest(BaseModel):
    ticket_id: int = Field(gt=0)
    request: str = Field(min_length=1, max_length=4_000)