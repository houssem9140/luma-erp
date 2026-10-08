app_name = "luma_erp"
app_title = "Luma ERP"
app_publisher = "Luma ERP"
app_description = "Business operations and ERP extensions for Luma ERP."
app_email = "maintainers@luma-erp.local"
app_license = "GNU General Public License (v3)"

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/luma_erp/images/luma-logo.svg",
		"title": app_title,
		"route": "/app/luma-erp",
	}
]

before_install = "luma_erp.install.before_install"
after_install = "luma_erp.install.after_install"

doc_events = {
	"*": {
		"validate": "luma_erp.events.validate_document",
	}
}
