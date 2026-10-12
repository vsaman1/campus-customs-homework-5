# Campus Customs MCP Server

This FastMCP server gives every Homework 5 agent a shared, read-only way to retrieve evidence needed to resolve the open Campus Customs tickets. It uses `../data/campus_customs_new.db`, the working copy of the supplied database.

Tools:

- `get_ticket_101_order_fulfillment`: returns ticket 101, its requested size-S tee inventory record, and its linked reprint invoice with vendor details.
- `get_ticket_102_rent_payment_context`: returns ticket 102, its lease, the current desk date, cash balances, and recorded rent payments.
- `get_ticket_103_bulk_discount_context`: returns ticket 103, the matching size-M hoodie inventory record, and its recorded unit pricing.
- `list_open_tickets`: returns the current open-ticket queue for Boss routing.
- `get_ticket_context`: returns a ticket and the related inventory, pricing, invoice, lease, payment, cash, and operating-date records that apply.
- `get_inventory_for_sku`: returns every size-level inventory record for one SKU.
- `get_invoice_with_vendor`: returns an invoice with its vendor details.
- `get_lease_financial_context`: returns a lease, operating date, cash balances, and recorded rent payments.
- `update_ticket_status`: changes only a ticket's status after explicit human approval; it accepts `open`, `in_progress`, or `resolved`.
- `list_tickets`: returns all ticket records and their current statuses.
- `get_cash_account`: returns one current cash-account balance.
- `prepare_ticket_payment`: returns a lease or invoice payment for review without changing cash.
- `approve_ticket_payment`: records a reviewed payment and debits checking only when the backend supplies a named human approver.