import os

from site_config import SERVICE_LANDINGS, SITE_URL, analytics_script_tag


def build_service_landings():
    with open("service_landing_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    for svc in SERVICE_LANDINGS:
        html = template
        for key, value in svc.items():
            html = html.replace("{{" + key + "}}", value)
        html = html.replace("{{site_url}}", SITE_URL)
        html = html.replace("{{canonical}}", f"{SITE_URL}/{svc['file']}.html")
        html = html.replace("{{prefix}}", "")
        html = html.replace("{{analytics_script}}", analytics_script_tag(""))

        path = f"{svc['file']}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    print(f"Generated {len(SERVICE_LANDINGS)} service landing pages.")


if __name__ == "__main__":
    build_service_landings()
