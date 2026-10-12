from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, FastMCPClient, MCPToolset
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

try:
    from .audit import append_audit_entry
    from .models import AgentRole, AuditEntry, TicketRunRequest
except ImportError:
    from audit import append_audit_entry
    from models import AgentRole, AuditEntry, TicketRunRequest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PATH = PROJECT_ROOT / "backend" / "prompts"
MCP_CONFIG_PATH = PROJECT_ROOT / ".mcp.json"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
PORTKEY_USER_AGENT = "campus-customs/1.0"
MODEL_NAME = "gpt-6-luna"
MAX_DELEGATION_DEPTH = 2


@dataclass(frozen=True)
class TeamDependencies:
    role: AgentRole
    delegation_depth: int = 0
    parent_role: AgentRole | None = None

    def for_child(self, role: AgentRole) -> "TeamDependencies":
        return TeamDependencies(
            role=role,
            delegation_depth=self.delegation_depth + 1,
            parent_role=self.role,
        )


class PortkeyPreflightError(RuntimeError):
    """Raised when the configured Portkey credentials cannot pass the required preflight."""


def _load_prompt(role: AgentRole) -> str:
    return (PROMPTS_PATH / f"{role.value}.md").read_text(encoding="utf-8")


def _portkey_model() -> OpenAIChatModel:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    api_key = os.environ.get("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the project-root .env file.")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={
            "x-portkey-api-key": api_key,
            "User-Agent": PORTKEY_USER_AGENT,
        },
    )
    provider = OpenAIProvider(openai_client=client)
    return OpenAIChatModel(MODEL_NAME, provider=provider)


def _portkey_preflight() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    api_key = os.environ.get("PORTKEY_API_KEY", "").strip()
    request = Request(
        f"{PORTKEY_BASE_URL}/models",
        headers={
            "x-portkey-api-key": api_key,
            "User-Agent": PORTKEY_USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise PortkeyPreflightError(f"Portkey preflight failed with HTTP {response.status}.")
    except HTTPError as error:
        raise PortkeyPreflightError(f"Portkey preflight was rejected with HTTP {error.code}. Check PORTKEY_API_KEY.") from error
    except URLError as error:
        raise PortkeyPreflightError("Portkey preflight could not reach the API.") from error


async def _audit_mcp_tool_call(
    context: RunContext[TeamDependencies], call_tool: CallToolFunc, tool_name: str, arguments: dict[str, object]
) -> object:
    role = context.deps.role
    append_audit_entry(
        AuditEntry(
            timestamp=datetime.now(UTC),
            agent=role,
            action="mcp_tool_called",
            task=f"MCP tool call: {tool_name}",
            parent_agent=context.deps.parent_role,
            delegation_depth=context.deps.delegation_depth,
            outcome="started",
            tool_name=tool_name,
            tool_arguments=arguments,
        )
    )
    try:
        result = await call_tool(tool_name, arguments)
    except Exception as error:
        append_audit_entry(
            AuditEntry(
                timestamp=datetime.now(UTC),
                agent=role,
                action="mcp_tool_failed",
                task=f"MCP tool call: {tool_name}",
                parent_agent=context.deps.parent_role,
                delegation_depth=context.deps.delegation_depth,
                outcome=f"{type(error).__name__}: {error}",
                tool_name=tool_name,
                tool_arguments=arguments,
            )
        )
        raise
    append_audit_entry(
        AuditEntry(
            timestamp=datetime.now(UTC),
            agent=role,
            action="mcp_tool_completed",
            task=f"MCP tool call: {tool_name}",
            parent_agent=context.deps.parent_role,
            delegation_depth=context.deps.delegation_depth,
            outcome="completed",
            tool_name=tool_name,
            tool_arguments=arguments,
        )
    )
    return result


class CampusCustomsTeam:
    def __init__(self) -> None:
        model = _portkey_model()
        config = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
        self.mcp_toolset = MCPToolset(FastMCPClient(config), process_tool_call=_audit_mcp_tool_call)
        self.agents = {
            role: Agent(
                model,
                system_prompt=_load_prompt(role),
                deps_type=TeamDependencies,
                name=role.value,
                toolsets=[self.mcp_toolset],
                model_settings={"openai_reasoning_effort": "none"},
                retries=1,
            )
            for role in AgentRole
        }
        for role, agent in self.agents.items():
            self._register_delegation_tool(agent, role)

    def _register_delegation_tool(self, agent: Agent[TeamDependencies, str], source_role: AgentRole) -> None:
        @agent.tool
        async def delegate_to_teammate(
            context: RunContext[TeamDependencies], target: AgentRole, task: str
        ) -> str:
            """Delegate a bounded, evidence-based subtask to any Campus Customs teammate."""
            if target == source_role:
                return "Do not delegate a task to the same role; continue the work directly."
            if context.deps.delegation_depth >= MAX_DELEGATION_DEPTH:
                return "Delegation depth limit reached. Use the MCP evidence already available and report the limit."
            return await self._run_agent(target, task, context.deps.for_child(target))

    async def run_ticket(self, request: TicketRunRequest) -> str:
        _portkey_preflight()
        task = (
            f"Handle ticket {request.ticket_id}. The user request is: {request.request}\n"
            "Start by using MCP tools to retrieve the ticket and related shop evidence. "
            "Do not make a customer, inventory, payment, or ticket-status change without explicit human approval."
        )
        async with self.mcp_toolset:
            return await self._run_agent(AgentRole.BOSS, task, TeamDependencies(role=AgentRole.BOSS))

    async def _run_agent(self, role: AgentRole, task: str, dependencies: TeamDependencies) -> str:
        started = perf_counter()
        append_audit_entry(
            AuditEntry(
                timestamp=datetime.now(UTC),
                agent=role,
                action="agent_loop_started",
                task=task,
                parent_agent=dependencies.parent_role,
                delegation_depth=dependencies.delegation_depth,
                outcome="started",
            )
        )
        try:
            result = await self.agents[role].run(task, deps=dependencies)
            output = str(result.output)
            append_audit_entry(
                AuditEntry(
                    timestamp=datetime.now(UTC),
                    agent=role,
                    action="agent_loop_completed",
                    task=task,
                    parent_agent=dependencies.parent_role,
                    delegation_depth=dependencies.delegation_depth,
                    outcome=f"completed in {perf_counter() - started:.2f}s: {output[:500]}",
                )
            )
            return output
        except Exception as error:
            append_audit_entry(
                AuditEntry(
                    timestamp=datetime.now(UTC),
                    agent=role,
                    action="agent_loop_failed",
                    task=task,
                    parent_agent=dependencies.parent_role,
                    delegation_depth=dependencies.delegation_depth,
                    outcome=f"failed in {perf_counter() - started:.2f}s: {type(error).__name__}: {error}",
                )
            )
            raise