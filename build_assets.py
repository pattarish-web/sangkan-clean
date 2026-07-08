"""Generate shared JS assets from site_config."""

from site_config import ADS_CONVERSION_ID, ADS_LEAD_CONVERSION_LABEL, GA4_MEASUREMENT_ID, analytics_script_tag


def _has_ga4():
    return bool(GA4_MEASUREMENT_ID and GA4_MEASUREMENT_ID != "G-PLACEHOLDER")


def write_analytics_js():
    """Keep analytics.js in sync for legacy references."""
    ads_label = ADS_LEAD_CONVERSION_LABEL.replace("'", "")
    primary = GA4_MEASUREMENT_ID if _has_ga4() else ADS_CONVERSION_ID
    ga4_config = (
        f"gtag('config','{GA4_MEASUREMENT_ID}');"
        if _has_ga4()
        else ""
    )
    content = f"""(function(){{
  var ads='{ADS_CONVERSION_ID}';
  var adsLeadLabel='{ads_label}';
  var s=document.createElement('script');
  s.async=true;
  s.src='https://www.googletagmanager.com/gtag/js?id={primary}';
  document.head.appendChild(s);
  window.dataLayer=window.dataLayer||[];
  function gtag(){{dataLayer.push(arguments);}}
  window.gtag=gtag;
  gtag('js',new Date());
  {ga4_config}
  gtag('config',ads);
  window.adsLeadSendTo=adsLeadLabel?ads+'/'+adsLeadLabel:'';
}})();
"""
    with open("analytics.js", "w", encoding="utf-8") as f:
        f.write(content)


def patch_root_html_files():
    """Replace deferred analytics.js with inline gtag on hand-maintained root pages."""
    import re

    snippet = analytics_script_tag("")
    files = {
        "index.html": (
            r'    <script src="analytics\.js" defer></script>\s*\n',
            snippet + "\n",
        ),
        "blog.html": (
            r'    <script src="analytics\.js" defer></script>\s*\n',
            snippet + "\n",
        ),
        "privacy.html": (
            r'    <script src="analytics\.js" defer></script>\s*\n',
            snippet + "\n",
        ),
        "landing-bigcleaning.html": (
            r'    <script src="analytics\.js" defer></script>\s*\n',
            snippet + "\n",
        ),
        "landing-maid.html": (
            r'    <script src="analytics\.js" defer></script>\s*\n',
            snippet + "\n",
        ),
    }
    for path, (pattern, replacement) in files.items():
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        html = re.sub(pattern, replacement, html, count=1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
