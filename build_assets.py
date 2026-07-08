"""Generate shared JS assets from site_config."""

from site_config import ADS_CONVERSION_ID, GA4_MEASUREMENT_ID


def write_analytics_js():
    ga4_line = (
        f"gtag('config','{GA4_MEASUREMENT_ID}');"
        if GA4_MEASUREMENT_ID and GA4_MEASUREMENT_ID != "G-PLACEHOLDER"
        else ""
    )
    content = f"""(function(){{
  var ads='{ADS_CONVERSION_ID}';
  var ga4='{GA4_MEASUREMENT_ID}';
  var s=document.createElement('script');
  s.async=true;
  s.src='https://www.googletagmanager.com/gtag/js?id='+ads;
  document.head.appendChild(s);
  window.dataLayer=window.dataLayer||[];
  function gtag(){{dataLayer.push(arguments);}}
  window.gtag=gtag;
  gtag('js',new Date());
  gtag('config',ads);
  {ga4_line}
}})();
"""
    with open("analytics.js", "w", encoding="utf-8") as f:
        f.write(content)
