# Luma ERP application

This is the custom Frappe application owned by the Luma ERP project.
ERPNext remains an upstream dependency; Luma-specific behavior belongs here
instead of modifying ERPNext core.

## Initial API

After installation, an authenticated request to
`/api/method/luma_erp.api.health` returns the application health status.
