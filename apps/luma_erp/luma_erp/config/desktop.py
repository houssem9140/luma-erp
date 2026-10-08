from frappe import _


def get_data() -> list[dict[str, object]]:
	return [
		{
			"module_name": "Luma Core",
			"category": "Modules",
			"type": "module",
			"label": _("Luma Core"),
			"color": "blue",
			"icon": "setting-gear",
			"link": "modules/luma_core",
			"onboard": 1,
		}
	]
