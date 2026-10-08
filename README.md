# Luma ERP

Luma ERP is an independent portfolio project built on the Frappe/ERPNext
technology stack. It will provide a rebranded, documented, and progressively
customized ERP platform for demonstration purposes.

## Development environment

The local development stack runs with Docker Desktop and includes:

- Frappe and ERPNext
- MariaDB
- Redis
- background workers
- scheduler and websocket services

Start the disposable development environment from the repository root:

```powershell
docker compose -f deployment\docker-compose.yml up -d
```

Open <http://localhost:8080> and sign in with:

- User: `Administrator`
- Password: `admin`

This compose file is based on the official Frappe Docker disposable setup.
It is intended for local development only. Persistent named Docker volumes
are created for the database, sites, logs, and queues.

## Project status

The initial runtime is validated. Luma currently includes master data for
organizations, customers, suppliers, and items, plus sales and purchase order
workflows and an inventory foundation for warehouses and stock entries, all
with automated validation tests. Inventory balances are updated when stock
entries are submitted and reversed when they are cancelled. Demo data, accounting, and production
deployment configuration are planned next.
Customer and supplier invoicing are now included with line totals, invoice
status, and outstanding amount tracking.

## Licensing and attribution

Luma ERP contains code derived from ERPNext and remains subject to the
GNU General Public License v3. See [LICENSE](LICENSE) and
[NOTICE.md](NOTICE.md).
