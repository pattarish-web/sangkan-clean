"""Generate shared JS assets from site_config."""

from site_config import ADS_CONVERSION_ID, ADS_LEAD_CONVERSION_LABEL, GA4_MEASUREMENT_ID


def _has_ga4():
    return bool(GA4_MEASUREMENT_ID and GA4_MEASUREMENT_ID != "G-PLACEHOLDER")


def write_analytics_js():
    has_ga4 = _has_ga4()
    primary_id = GA4_MEASUREMENT_ID if has_ga4 else ADS_CONVERSION_ID
    ga4_config = (
        f"gtag('config','{GA4_MEASUREMENT_ID}',{{send_page_view:true}});"
        if has_ga4
        else ""
    )
    ads_label = ADS_LEAD_CONVERSION_LABEL.replace("'", "")
    content = f"""(function(){{
  var ads='{ADS_CONVERSION_ID}';
  var ga4='{GA4_MEASUREMENT_ID}';
  var adsLeadLabel='{ads_label}';
  var primary='{primary_id}';
  var s=document.createElement('script');
  s.async=true;
  s.src='https://www.googletagmanager.com/gtag/js?id='+primary;
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
