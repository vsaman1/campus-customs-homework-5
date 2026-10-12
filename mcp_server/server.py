from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "campus_customs_new.db"
mcp = FastMCP("Campus Customs")


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{DATABASE_PATH.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _write_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _one(connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...]) -> dict[str, Any] | None:
    row = connection.execute(query, parameters).fetchone()
    return dict(row) if row else None


def _all(connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, parameters)]


@mcp.tool
def get_ticket_101_order_fulfillment() -> dict[str, Any]:
    """Return the requested tee, its size-S stock, and ticket 101's linked reprint invoice."""
    with _connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (101,))
        if ticket is None:
            return {"error": "Ticket 101 was not found."}

        return {
            "ticket": ticket,
            "requested_inventory": _one(
                connection,
                "SELECT * FROM inventory WHERE sku = ? AND size = ?",
                (ticket["sku"], ticket["size"]),
            ),
            "linked_invoice": _one(
                connection,
                """
                SELECT invoices.*, vendors.name AS vendor_name, vendors.specialty, vendors.lead_days
                FROM invoices
                JOIN vendors ON vendors.id = invoices.vendor_id
                WHERE invoices.id = ?
                """,
                (ticket["invoice_id"],),
            ),
        }


@mcp.tool
def get_ticket_102_rent_payment_context() -> dict[str, Any]:
    """Return ticket 102's lease, current desk date, cash balance, and recorded rent payments."""
    with _connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (102,))
        if ticket is None:
            return {"error": "Ticket 102 was not found."}

        return {
            "ticket": ticket,
            "lease": _one(connection, "SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],)),
            "today": _one(connection, "SELECT * FROM desk LIMIT 1", ()),
            "cash_accounts": _all(connection, "SELECT * FROM cash_accounts ORDER BY name"),
            "rent_payments": _all(
                connection,
                "SELECT * FROM payments WHERE kind LIKE ? OR ref_id = ? ORDER BY paid_at",
                ("%rent%", ticket["lease_id"]),
            ),
        }


@mcp.tool
def get_ticket_103_bulk_discount_context() -> dict[str, Any]:
    """Return ticket 103's hoodie request, matching size-M stock, and recorded unit pricing."""
    with _connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (103,))
        if ticket is None:
            return {"error": "Ticket 103 was not found."}

        return {
            "ticket": ticket,
            "requested_inventory": _one(
                connection,
                "SELECT * FROM inventory WHERE sku = ? AND size = ?",
                (ticket["sku"], ticket["size"]),
            ),
            "pricing": _one(connection, "SELECT * FROM pricing WHERE sku = ?", (ticket["sku"],)),
        }


@mcp.tool
def list_open_tickets() -> list[dict[str, Any]]:
    """Return every currently open ticket so the Boss can route work from the live queue."""
    with _connection() as connection:
        return _all(connection, "SELECT * FROM tickets WHERE status = ? ORDER BY id", ("open",))


@mcp.tool
def get_ticket_context(ticket_id: int) -> dict[str, Any]:
    """Return one ticket and its related inventory, pricing, invoice, lease, and payment evidence."""
    with _connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if ticket is None:
            return {"error": f"Ticket {ticket_id} was not found."}

        context: dict[str, Any] = {"ticket": ticket}
        if ticket["sku"] is not None:
            context["inventory"] = _all(
                connection,
                "SELECT * FROM inventory WHERE sku = ? ORDER BY size",
                (ticket["sku"],),
            )
            context["pricing"] = _one(connection, "SELECT * FROM pricing WHERE sku = ?", (ticket["sku"],))
        if ticket["invoice_id"] is not None:
            context["invoice"] = _one(
                connection,
                """
                SELECT invoices.*, vendors.name AS vendor_name, vendors.specialty, vendors.lead_days
                FROM invoices
                JOIN vendors ON vendors.id = invoices.vendor_id
                WHERE invoices.id = ?
                """,
                (ticket["invoice_id"],),
            )
        if ticket["lease_id"] is not None:
            context["lease"] = _one(connection, "SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],))
            context["rent_payments"] = _all(
                connection,
                "SELECT * FROM payments WHERE kind LIKE ? OR ref_id = ? ORDER BY paid_at",
                ("%rent%", ticket["lease_id"]),
            )
            context["cash_accounts"] = _all(connection, "SELECT * FROM cash_accounts ORDER BY name")
            context["desk"] = _one(connection, "SELECT * FROM desk LIMIT 1", ())
        return context


@mcp.tool
def get_inventory_for_sku(sku: str) -> list[dict[str, Any]]:
    """Return all size-level inventory records for a SKU without changing stock."""
    with _connection() as connection:
        return _all(connection, "SELECT * FROM inventory WHERE sku = ? ORDER BY size", (sku,))


@mcp.tool
def get_invoice_with_vendor(invoice_id: int) -> dict[str, Any]:
    """Return a vendor invoice and its vendor details for accounting review."""
    with _connection() as connection:
        invoice = _one(
            connection,
            """
            SELECT invoices.*, vendors.name AS vendor_name, vendors.specialty, vendors.lead_days
            FROM invoices
            JOIN vendors ON vendors.id = invoices.vendor_id
            WHERE invoices.id = ?
            """,
            (invoice_id,),
        )
        return invoice or {"error": f"Invoice {invoice_id} was not found."}


@mcp.tool
def get_lease_financial_context(lease_id: int) -> dict[str, Any]:
    """Return a lease, current operating date, cash balances, and related recorded rent payments."""
    with _connection() as connection:
        lease = _one(connection, "SELECT * FROM leases WHERE id = ?", (lease_id,))
        if lease is None:
            return {"error": f"Lease {lease_id} was not found."}
        return {
            "lease": lease,
            "today": _one(connection, "SELECT * FROM desk LIMIT 1", ()),
            "cash_accounts": _all(connection, "SELECT * FROM cash_accounts ORDER BY name"),
            "rent_payments": _all(
                connection,
                "SELECT * FROM payments WHERE kind LIKE ? OR ref_id = ? ORDER BY paid_at",
                ("%rent%", lease_id),
            ),
        }


@mcp.tool
def update_ticket_status(ticket_id: int, status: str) -> dict[str, Any]:
    """Set a ticket to open, in_progress, or resolved after explicit human approval."""
    allowed_statuses = {"open", "in_progress", "resolved"}
    if status not in allowed_statuses:
        return {"error": f"Status must be one of: {', '.join(sorted(allowed_statuses))}."}

    with _write_connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if ticket is None:
            return {"error": f"Ticket {ticket_id} was not found."}
        connection.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        updated_ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return {"before": ticket, "after": updated_ticket}


@mcp.tool
def list_tickets() -> list[dict[str, Any]]:
    """Return all tickets and their live statuses for the operations dashboard."""
    with _connection() as connection:
        return _all(connection, "SELECT * FROM tickets ORDER BY id")


@mcp.tool
def get_cash_account(account_name: str = "checking") -> dict[str, Any]:
    """Return the current balance and date for one cash account."""
    with _connection() as connection:
        account = _one(connection, "SELECT * FROM cash_accounts WHERE name = ?", (account_name,))
        return account or {"error": f"Cash account '{account_name}' was not found."}


@mcp.tool
def prepare_ticket_payment(ticket_id: int) -> dict[str, Any]:
    """Return the exact invoice or rent payment a human may review, without changing cash."""
    with _connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if ticket is None:
            return {"error": f"Ticket {ticket_id} was not found."}

        if ticket["invoice_id"] is not None:
            invoice = _one(connection, "SELECT * FROM invoices WHERE id = ?", (ticket["invoice_id"],))
            if invoice is None:
                return {"error": f"Invoice {ticket['invoice_id']} was not found."}
            payment = {"kind": "invoice_payment", "ref_id": invoice["id"], "amount": invoice["amount"]}
        elif ticket["lease_id"] is not None:
            lease = _one(connection, "SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],))
            if lease is None:
                return {"error": f"Lease {ticket['lease_id']} was not found."}
            payment = {"kind": "rent_payment", "ref_id": lease["id"], "amount": lease["monthly_rent"]}
        else:
            return {"error": f"Ticket {ticket_id} has no invoice or lease payment to prepare."}

        return {
            "ticket": ticket,
            "payment": payment,
            "cash_account": _one(connection, "SELECT * FROM cash_accounts WHERE name = ?", ("checking",)),
            "approval_required": True,
        }


@mcp.tool
def approve_ticket_payment(ticket_id: int, approved_by: str) -> dict[str, Any]:
    """Apply a prepared ticket payment only after a named human has approved it."""
    approver = approved_by.strip()
    if not approver:
        return {"error": "A named human approver is required."}

    with _write_connection() as connection:
        ticket = _one(connection, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if ticket is None:
            return {"error": f"Ticket {ticket_id} was not found."}

        if ticket["invoice_id"] is not None:
            invoice = _one(connection, "SELECT * FROM invoices WHERE id = ?", (ticket["invoice_id"],))
            if invoice is None:
                return {"error": f"Invoice {ticket['invoice_id']} was not found."}
            kind, ref_id, amount = "invoice_payment", invoice["id"], invoice["amount"]
        elif ticket["lease_id"] is not None:
            lease = _one(connection, "SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],))
            if lease is None:
                return {"error": f"Lease {ticket['lease_id']} was not found."}
            kind, ref_id, amount = "rent_payment", lease["id"], lease["monthly_rent"]
        else:
            return {"error": f"Ticket {ticket_id} has no invoice or lease payment to approve."}

        existing_payment = _one(
            connection,
            "SELECT * FROM payments WHERE kind = ? AND ref_id = ? ORDER BY id DESC LIMIT 1",
            (kind, ref_id),
        )
        if existing_payment is not None:
            return {"error": "This payment has already been recorded.", "payment": existing_payment}

        cash_account = _one(connection, "SELECT * FROM cash_accounts WHERE name = ?", ("checking",))
        if cash_account is None:
            return {"error": "Checking account was not found."}
        if cash_account["balance"] < amount:
            return {"error": "Checking balance is insufficient for this payment.", "cash_account": cash_account}

        desk = _one(connection, "SELECT * FROM desk LIMIT 1", ())
        paid_at = desk["date_today"] if desk else ""
        cursor = connection.execute(
            """
            INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (kind, ref_id, amount, "checking", paid_at, approver),
        )
        connection.execute(
            "UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ?",
            (amount, paid_at, "checking"),
        )
        if ticket["invoice_id"] is not None:
            connection.execute("UPDATE invoices SET status = ? WHERE id = ?", ("paid", ticket["invoice_id"]))

        return {
            "ticket": ticket,
            "payment": _one(connection, "SELECT * FROM payments WHERE id = ?", (cursor.lastrowid,)),
            "cash_account": _one(connection, "SELECT * FROM cash_accounts WHERE name = ?", ("checking",)),
        }


if __name__ == "__main__":
    mcp.run()