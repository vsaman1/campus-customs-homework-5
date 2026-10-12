from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .audit import append_audit_entry, recent_audit_entries
    from .mcp_gateway import call_mcp_tool
    from .models import AgentRole, AuditEntry, TicketRunRequest
    from .team import CampusCustomsTeam, PortkeyPreflightError
except ImportError:
    from audit import append_audit_entry, recent_audit_entries
    from mcp_gateway import call_mcp_tool
    from models import AgentRole, AuditEntry, TicketRunRequest
    from team import CampusCustomsTeam, PortkeyPreflightError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATABASE = PROJECT_ROOT / "data" / "campus_customs.db"
WORKING_DATABASE = PROJECT_ROOT / "data" / "campus_customs_new.db"

app = FastAPI(title="Campus Customs Operations API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PaymentApproval(BaseModel):
    approved_by: str = Field(min_length=1, max_length=120)


class StatusApproval(BaseModel):
    approved_by: str = Field(min_length=1, max_length=120)


@app.get("/tickets")
async def tickets() -> list[dict[str, object]]:
    response = await call_mcp_tool("list_tickets")
    records = response["result"]
    return [
        {
            "id": record["id"],
            "type": record["type"],
            "subject": record["subject"],
            "requester": record["requester"],
            "status": record["status"],
            "is_open": record["status"] == "open",
            "is_resolved": record["status"] == "resolved",
        }
        for record in records
    ]


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int, request: TicketRunRequest) -> dict[str, object]:
    if request.ticket_id != ticket_id:
        raise HTTPException(status_code=422, detail="Ticket id must match the request body.")
    try:
        result = await CampusCustomsTeam().run_ticket(request)
    except PortkeyPreflightError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"ticket_id": ticket_id, "result": result}


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: int, approval: StatusApproval) -> dict[str, object]:
    result = await call_mcp_tool("update_ticket_status", {"ticket_id": ticket_id, "status": "resolved"})
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    append_audit_entry(
        AuditEntry(
            timestamp=datetime.now(UTC),
            agent=AgentRole.BOSS,
            action="ticket_resolved",
            task=f"Ticket {ticket_id} status update",
            delegation_depth=0,
            outcome=f"Human approval by {approval.approved_by}; MCP updated ticket status to resolved.",
            tool_name="update_ticket_status",
            tool_arguments={"ticket_id": ticket_id, "status": "resolved", "approved_by": approval.approved_by},
        )
    )
    return result


@app.get("/events")
async def events(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, object]]:
    return recent_audit_entries(limit)


@app.get("/tickets/{ticket_id}/payment-preparation")
async def payment_preparation(ticket_id: int) -> dict[str, object]:
    result = await call_mcp_tool("prepare_ticket_payment", {"ticket_id": ticket_id})
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@app.post("/tickets/{ticket_id}/approve-payment")
async def approve_payment(ticket_id: int, approval: PaymentApproval) -> dict[str, object]:
    result = await call_mcp_tool(
        "approve_ticket_payment",
        {"ticket_id": ticket_id, "approved_by": approval.approved_by},
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    payment = result["payment"]
    cash_account = result["cash_account"]
    append_audit_entry(
        AuditEntry(
            timestamp=datetime.now(UTC),
            agent=AgentRole.ACCOUNTING,
            action="human_payment_approved",
            task=f"Human approval for Ticket {ticket_id} payment",
            delegation_depth=0,
            outcome=(
                f"{payment['kind']} payment {payment['id']} for ${payment['amount']:.2f} was approved by "
                f"{approval.approved_by}; checking is now ${cash_account['balance']:.2f}."
            ),
            tool_name="approve_ticket_payment",
            tool_arguments={"ticket_id": ticket_id, "approved_by": approval.approved_by},
        )
    )
    return result


@app.get("/cash/checking")
async def checking_balance() -> dict[str, object]:
    result = await call_mcp_tool("get_cash_account", {"account_name": "checking"})
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/reset")
async def reset_database() -> dict[str, object]:
    if not SOURCE_DATABASE.exists():
        raise HTTPException(status_code=500, detail="Original database is unavailable.")
    copy2(SOURCE_DATABASE, WORKING_DATABASE)
    return {"reset": True, "database": "data/campus_customs_new.db"}