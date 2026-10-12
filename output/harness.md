# Campus Customs Harness

## Problem 2 — Campus Customs Database Study

### Tables

| Table | Fields | Why it matters |
| --- | --- | --- |
| `cash_accounts` | `name` (TEXT, PK), `balance` (REAL), `date` (TEXT) | Shows the cash available when deciding whether the business can make a payment. |
| `desk` | `date_today` (TEXT), `notes` (TEXT) | Supplies the operating date needed to interpret due dates and ticket timing. |
| `inventory` | `sku` (TEXT, PK), `name` (TEXT), `size` (TEXT, PK), `qty` (INTEGER), `location` (TEXT) | Shows whether the exact product, size, and quantity requested by a customer are available. |
| `invoices` | `id` (INTEGER, PK), `vendor_id` (INTEGER), `amount` (REAL), `due_date` (TEXT), `status` (TEXT), `description` (TEXT) | Tracks vendor obligations, including the reprint invoice linked to ticket 101. |
| `leases` | `id` (INTEGER, PK), `space_name` (TEXT), `landlord` (TEXT), `monthly_rent` (REAL), `next_due` (TEXT), `notes` (TEXT) | Defines the rent amount and due date behind the ticket 102 notice. |
| `payments` | `id` (INTEGER, PK), `kind` (TEXT), `ref_id` (INTEGER), `amount` (REAL), `account` (TEXT), `paid_at` (TEXT), `approved_by` (TEXT) | Provides the payment history needed to determine whether an obligation has already been paid. |
| `pricing` | `sku` (TEXT, PK), `unit_cost` (REAL), `list_price` (REAL) | Provides the recorded cost and list price needed to evaluate the ticket 103 discount request. |
| `tickets` | `id` (INTEGER, PK), `type` (TEXT), `requester` (TEXT), `subject` (TEXT), `sku` (TEXT), `size` (TEXT), `qty` (INTEGER), `lease_id` (INTEGER), `invoice_id` (INTEGER), `status` (TEXT), `notes` (TEXT), `created_at` (TEXT) | Is the agent's work queue and connects each request to its relevant inventory, lease, or invoice record. |
| `vendors` | `id` (INTEGER, PK), `name` (TEXT), `specialty` (TEXT), `lead_days` (INTEGER) | Identifies the vendor and turnaround information for invoice-backed fulfillment work. |

### Open Ticket Links

- Ticket 101 requests one `CC-TEE-WHITE` in size `S`; it links to invoice 501, a rush reprint for that same SKU and size.
- Ticket 102 links to lease 1 for the Chapel Street shop and is a rent notice from its landlord.
- Ticket 103 requests 20 `CC-HOOD-NAVY` hoodies in size `M` and needs inventory and pricing evidence for its bulk-discount request.

## Problem 3 — Ticket Resolution MCP Server

| Tool | Tables read | Ticket unlocked | Why this is the right tool |
| --- | --- | --- | --- |
| `get_ticket_101_order_fulfillment` | `tickets`, `inventory`, `invoices`, `vendors` | 101 | Ticket 101 requests a size-S `CC-TEE-WHITE`; the tool returns that exact stock record and the linked rush-reprint invoice 501 with its vendor's lead time. |
| `get_ticket_102_rent_payment_context` | `tickets`, `leases`, `desk`, `cash_accounts`, `payments` | 102 | Ticket 102 says rent is due in two days; the tool combines its lease's rent and due date with the current desk date, available cash, and any recorded rent payment. |
| `get_ticket_103_bulk_discount_context` | `tickets`, `inventory`, `pricing` | 103 | Ticket 103 asks for 20 size-M `CC-HOOD-NAVY` hoodies at a discount; the tool returns the exact size-M stock and the SKU's recorded unit cost and list price. |

## Problem 5 — Campus Customs Agent Team

### Agents

| Agent | Responsibility |
| --- | --- |
| Boss | Routes tickets, delegates specialist work, reconciles MCP evidence, and presents an approval-aware final recommendation. |
| Inventory | Verifies SKU, size, quantity, location, supply constraints, and reprint evidence without promising stock or delivery. |
| Accounting | Reviews invoices, payments, cash, leases, and recorded pricing without authorizing money or price changes. |
| Facilities | Reviews landlord, lease, rent due date, operating date, and recorded rent-payment context. |
| Customer Service | Drafts customer-safe responses from verified MCP facts without exposing internal information or making unsupported commitments. |

Every agent shares the same MCP toolset and can delegate a bounded subtask to any other role. Agent-loop start, completion, and failure events append to `output/audit_trail.json`.

### Added MCP Tools

| Tool | Tables used |
| --- | --- |
| `list_open_tickets` | `tickets` |
| `get_ticket_context` | `tickets`, `inventory`, `pricing`, `invoices`, `vendors`, `leases`, `payments`, `cash_accounts`, `desk` |
| `get_inventory_for_sku` | `inventory` |
| `get_invoice_with_vendor` | `invoices`, `vendors` |
| `get_lease_financial_context` | `leases`, `desk`, `cash_accounts`, `payments` |
| `update_ticket_status` | `tickets` |

### Safety and Token Limits

- Agents use only MCP tools for shop facts and database access; they do not create a second data-access layer.
- They do not expose customer or business-sensitive details, invent commitments, send messages, reserve stock, make payments, change prices, or change ticket status without explicit human approval.
- The Boss requires tool-backed evidence and records every loop step in the append-only audit trail.
- Delegation depth is capped at two hops, each agent has one retry, and prompts require focused ticket-scoped work to limit unnecessary model and tool use.

## Problem 7 — Backend Routes

- `GET /tickets`: returns the three tickets with their current status and open/resolved flags.
- `POST /tickets/{ticket_id}/run`: runs the PydanticAI team for the matching ticket body after a Portkey preflight.
- `POST /tickets/{ticket_id}/resolve`: marks a successfully completed ticket resolved through the MCP status tool.
- `GET /events?limit=50`: returns recent agent-loop messages and MCP tool-use audit events.
- `GET /tickets/{ticket_id}/payment-preparation`: returns a payment proposal without changing cash.
- `POST /tickets/{ticket_id}/approve-payment`: records a payment and changes checking only after a named human approval.
- `GET /cash/checking`: returns the current checking-account balance.
- `POST /reset`: restores `data/campus_customs_new.db` from the original supplied database without clearing the append-only audit trail.

## Problem 8 — Agent Dashboard

- React/Vite/TypeScript dashboard in `frontend/` consumes the Problem 7 API at `http://localhost:8000`.
- The ticket rail shows all tickets and their open/resolved state; selecting a ticket refreshes its payment proposal and audit events.
- The agent relay polls events, while the summary identifies each role's most recent recorded outcome for the selected ticket.
- Runs with a payment proposal stop at the separate human approval panel. Approval is the only UI action that spends cash; it then resolves the ticket and refreshes the displayed checking balance.

## Problem 9 — Live Team Run

- Portkey preflight and a minimal `gpt-6-luna` chat-completions request succeeded before ticket processing.
- Clean rerun: Ticket 101 used Boss and Inventory with `get_ticket_101_order_fulfillment`; Ticket 102 used Boss and Accounting with ticket/rent context plus payment preparation; Ticket 103 used Boss, Inventory, and Accounting with `get_ticket_103_bulk_discount_context`.
- Human approvals: payment 1 for $840, payment 2 for $2,400, explicit Ticket 101/102 resolution authorizations, and Ticket 103's no-discount and 12-unit-shortfall decision are all recorded before their matching MCP status updates.
- Final verification: all three tickets are resolved. `payments` contains only the $840 invoice and $2,400 rent records with named human approval, and `cash_accounts.checking` is exactly $160.00.
- `output/audit_trail.json` remains append-only and preserves prior history while adding the clean-run marker, live agent/MCP events, approval events, customer-response draft, and all three final status updates.