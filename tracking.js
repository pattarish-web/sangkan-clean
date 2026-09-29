/** Capture gclid even when attribution.js 404s on GitHub Pages. */
if (!window.SangkanAttribution) {
/** First/last-touch attribution for Sangkan Clean. No PII. 90-day click window. */
(function () {
    var CLICK_MS = 90 * 24 * 60 * 60 * 1000;
    var FIRST_KEY = "sc_attr_first";
    var LAST_KEY = "sc_attr_last";
    var CLICK_KEYS = [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "gclid",
        "gbraid",
        "wbraid",
        "fbclid",
        "li_fat_id",
        "ttclid",
        "msclkid",
        "campaignid",
        "adgroupid",
        "creative",
        "keyword",
        "searchterm",
        "gad_source",
        "gad_campaignid",
    ];

    function now() {
        return Date.now();
    }

    function safeParse(raw) {
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function read(key) {
        try {
            return safeParse(localStorage.getItem(key));
        } catch (e) {
            return null;
        }
    }

    function write(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            /* private mode */
        }
    }

    function param(search, name) {
        try {
            var v = new URLSearchParams(search).get(name);
            return v ? String(v).slice(0, 180) : "";
        } catch (e) {
            return "";
        }
    }

    function cleanTrack(v) {
        if (!v) return "";
        if (v.charAt(0) === "{" && v.charAt(v.length - 1) === "}") return "";
        return v;
    }

    /* Google does not replace {searchterm}. Show matched {keyword} / utm_term instead. */
    function fillSearchterm(record) {
        if (!record || record.searchterm) return record;
        var fallback = record.utm_term || record.keyword || "";
        if (fallback) record.searchterm = fallback;
        return record;
    }

    function cookieValue(name) {
        try {
            var parts = String(document.cookie || "").split(";");
            for (var i = 0; i < parts.length; i++) {
                var row = parts[i].replace(/^\s+/, "");
                if (row.indexOf(name + "=") === 0) {
                    return decodeURIComponent(row.slice(name.length + 1));
                }
            }
        } catch (e) {
            return "";
        }
        return "";
    }

    /* Google Ads click cookies: GCL.<timestamp>.<gclid> */
    function gclId(name) {
        var raw = cookieValue(name);
        if (!raw) return "";
        var bits = raw.split(".");
        if (bits.length >= 3 && bits[0] === "GCL") return bits.slice(2).join(".").slice(0, 180);
        return "";
    }

    function referrerHost() {
        try {
            if (!document.referrer) return "";
            return new URL(document.referrer).host.slice(0, 120);
        } catch (e) {
            return "";
        }
    }

    function landingPath() {
        try {
            return (location.pathname || "/") + (location.hash || "");
        } catch (e) {
            return "/";
        }
    }

    function collectFromUrl() {
        var search = "";
        try {
            search = location.search || "";
        } catch (e) {
            search = "";
        }
        var out = {};
        var hasClick = false;
        for (var i = 0; i < CLICK_KEYS.length; i++) {
            var k = CLICK_KEYS[i];
            var v = cleanTrack(param(search, k));
            if (v) {
                out[k] = v;
                hasClick = true;
            }
        }
        if (!out.gclid) {
            var aw = gclId("_gcl_aw") || gclId("_gcl_dc");
            if (aw) {
                out.gclid = aw;
                hasClick = true;
            }
        }
        if (!out.gbraid) {
            var gb = gclId("_gcl_gb");
            if (gb) {
                out.gbraid = gb;
                hasClick = true;
            }
        }
        fillSearchterm(out);
        out.landing_page = landingPath();
        out.referrer = referrerHost();
        out.captured_at = now();
        out.has_click = hasClick;
        return out;
    }

    function expired(record) {
        if (!record || !record.captured_at) return true;
        return now() - Number(record.captured_at) > CLICK_MS;
    }

    function capture() {
        var current = collectFromUrl();
        var first = read(FIRST_KEY);
        var last = read(LAST_KEY);

        if (current.has_click) {
            /* Do not refresh first-touch expiry on repeat visits — 90 days from original click. */
            if (!first || expired(first)) {
                write(FIRST_KEY, current);
                first = current;
            }
            write(LAST_KEY, current);
            last = current;
        } else if (first && expired(first)) {
            first = null;
            write(FIRST_KEY, null);
        }

        return snapshot(first, last, current);
    }

    function pick(record, prefix) {
        var out = {};
        if (!record) return out;
        for (var i = 0; i < CLICK_KEYS.length; i++) {
            var k = CLICK_KEYS[i];
            if (record[k]) out[prefix + k] = record[k];
        }
        if (record.landing_page) out[prefix + "landing_page"] = record.landing_page;
        if (record.referrer) out[prefix + "referrer"] = record.referrer;
        if (record.captured_at) out[prefix + "captured_at"] = record.captured_at;
        return out;
    }

    function channelOf(record) {
        if (!record) return "direct";
        if (record.gclid || record.gbraid || record.wbraid || record.gad_source) return "google_ads";
        var src = String(record.utm_source || "").toLowerCase();
        var med = String(record.utm_medium || "").toLowerCase();
        if (src === "google" && /(cpc|ppc|paid|sem|paidsearch)/.test(med)) return "google_ads";
        if (record.fbclid) return "facebook";
        if (record.li_fat_id) return "line";
        if (record.ttclid) return "tiktok";
        if (record.msclkid) return "microsoft_ads";
        if (record.utm_source) return src;
        if (record.referrer) return "referral";
        return "direct";
    }

    function snapshot(first, last, current) {
        first = first || read(FIRST_KEY);
        last = last || read(LAST_KEY);
        current = current || collectFromUrl();
        if (first && expired(first)) first = null;
        var merged = {};
        var k;
        for (k in pick(first, "first_")) merged[k] = pick(first, "first_")[k];
        var lastPick = pick(last || current, "last_");
        for (k in lastPick) merged[k] = lastPick[k];
        merged.channel = channelOf(last || current || first);
        merged.first_channel = channelOf(first);
        merged.gclid = (last && last.gclid) || (first && first.gclid) || current.gclid || "";
        merged.gbraid = (last && last.gbraid) || (first && first.gbraid) || "";
        merged.wbraid = (last && last.wbraid) || (first && first.wbraid) || "";
        merged.utm_source = (last && last.utm_source) || (first && first.utm_source) || "";
        merged.utm_medium = (last && last.utm_medium) || (first && first.utm_medium) || "";
        merged.utm_campaign = (last && last.utm_campaign) || (first && first.utm_campaign) || "";
        merged.utm_content = (last && last.utm_content) || (first && first.utm_content) || "";
        merged.utm_term = (last && last.utm_term) || (first && first.utm_term) || "";
        merged.campaignid = (last && last.campaignid) || "";
        merged.adgroupid = (last && last.adgroupid) || "";
        merged.creative = (last && last.creative) || "";
        merged.keyword = (last && last.keyword) || (first && first.keyword) || "";
        merged.searchterm = (last && last.searchterm) || (first && first.searchterm) || current.searchterm || "";
        fillSearchterm(merged);
        merged.landing_page = current.landing_page;
        merged.referrer = current.referrer;
        return merged;
    }

    var captured = capture();

    window.SangkanAttribution = {
        capture: capture,
        snapshot: function () {
            return snapshot();
        },
        channelOf: channelOf,
        CLICK_MS: CLICK_MS,
        _collectFromUrl: collectFromUrl,
        _expired: expired,
    };

    try {
        window.__SC_ATTR__ = captured;
    } catch (e) {
        /* ignore */
    }
})();

}

/** Shared conversion tracking for Sangkan Clean (GA4 + Google Ads) */
(function () {
    function pagePath() {
        try {
            return window.location.pathname || '/';
        } catch (e) {
            return '/';
        }
    }

    window.trackEvent = function (eventName, params) {
        if (typeof gtag !== 'function') return;
        var payload = Object.assign({ page_path: pagePath() }, params || {});
        gtag('event', eventName, payload);
    };

    function adsSendTo(kind) {
        var map = window.adsConversions || {};
        if (kind && map[kind]) return map[kind];
        return ''; 
    }

    function fireAdsConversion(kind, extra) {
        /* Phone/LINE must not use this on click — staff confirms first, then offline import. */
        var sendTo = adsSendTo(kind);
        if (!sendTo) return false;
        var key = 'sc_ads_conv_' + kind + '_' + pagePath();
        try {
            if (sessionStorage.getItem(key) === '1') return false;
            sessionStorage.setItem(key, '1');
        } catch (e) { /* private mode */ }
        trackEvent('conversion', Object.assign({ send_to: sendTo }, extra || {}));
        return true;
    }

    function leadApiBase() {
        var configured = String(window.LEAD_API_URL || '').replace(/\/$/, '');
        if (configured) return configured;
        var host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
            return '/api/leads';
        }
        if (host === 'www.sangkanclean.com' || host === 'sangkanclean.com') {
            return 'https://sangkan-office-ops.onrender.com/api/leads';
        }
        return '';
    }

    function preserveClickIdsOnQuoteLinks() {
        var search = '';
        try {
            search = window.location.search || '';
        } catch (e) {
            return;
        }
        if (!search) return;
        document.querySelectorAll('a[href*="#quote"]').forEach(function (el) {
            var href = el.getAttribute('href') || '';
            if (!href || href.indexOf('?') !== -1) return;
            var parts = href.split('#');
            el.setAttribute('href', parts[0] + search + (parts[1] ? '#' + parts[1] : ''));
        });
    }

    function attributionSnapshot() {
        try {
            if (window.SangkanAttribution && window.SangkanAttribution.snapshot) {
                return window.SangkanAttribution.snapshot();
            }
        } catch (e) { /* attribution is best effort */ }
        return {};
    }

    function captureContactClick(method, el) {
        var base = leadApiBase();
        if (!base) return;

        var now = Date.now();
        var dedupeKey = 'sc_contact_click_' + method;
        try {
            var last = Number(sessionStorage.getItem(dedupeKey) || 0);
            if (now - last < 10000) return;
            sessionStorage.setItem(dedupeKey, String(now));
        } catch (e) { /* private mode */ }

        var payload = {
            contact_method: method,
            clicked_target: (el && el.getAttribute('href')) || '',
            page_path: pagePath(),
            attribution: attributionSnapshot(),
            idempotency_key:
                'click-' + method + '-' + now.toString(36) + '-' +
                Math.random().toString(36).slice(2, 7),
        };
        try {
            fetch(base + '/contact-click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true,
            }).catch(function () { /* never block phone/LINE navigation */ });
        } catch (e) { /* old browser: keep contact link working */ }
    }

    function bindClick(selector, eventName, extra) {
        document.querySelectorAll(selector).forEach(function (el) {
            if (el.dataset.gaBound === eventName) return;
            el.dataset.gaBound = eventName;
            el.addEventListener('click', function () {
                var params = Object.assign({ event_category: 'contact' }, extra || {});
                if (el.id) params.element_id = el.id;
                trackEvent(eventName, params);
            });
        });
    }

    function bindContactClicks() {
        bindClick('a[href^="tel:"]', 'click_phone', { method: 'phone' });
        bindClick('a[href*="line.me"]', 'click_line', { method: 'line' });
        bindClick('a[href*="m.me"]', 'click_messenger', { method: 'messenger' });
        bindClick('a[href*="facebook.com"]', 'click_facebook', { method: 'facebook' });

        document.querySelectorAll('a[href^="tel:"]').forEach(function (el) {
            if (el.dataset.adsPhoneBound) return;
            el.dataset.adsPhoneBound = '1';
            el.addEventListener('click', function () {
                captureContactClick('phone', el);
                /* Google Ads conversion waits until staff confirms the click in /ops/leads. */
            });
        });

        document.querySelectorAll('a[href*="line.me"]').forEach(function (el) {
            if (el.dataset.adsLineBound) return;
            el.dataset.adsLineBound = '1';
            el.addEventListener('click', function () {
                captureContactClick('line', el);
                /* Google Ads conversion waits until staff confirms the click in /ops/leads. */
            });
        });
    }

    function trackLeadSuccess() {
        var key = 'sc_lead_' + pagePath();
        try {
            if (sessionStorage.getItem(key) === '1') return;
            sessionStorage.setItem(key, '1');
        } catch (e) { /* private mode */ }

        trackEvent('quote_form_success', { event_category: 'lead', method: 'quote_form' });
        trackEvent('generate_lead', {
            method: 'quote_form',
            currency: 'THB',
            event_category: 'lead',
        });
        fireAdsConversion('lead', { event_category: 'lead', method: 'quote_form' });
    }

    document.addEventListener('DOMContentLoaded', function () {
        bindContactClicks();
        preserveClickIdsOnQuoteLinks();

        document.querySelectorAll('#hero-cta-line, #hero-cta-phone').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('hero_cta_click', {
                    event_category: 'contact',
                    element_id: el.id,
                });
            });
        });

        document.querySelectorAll('.blog-card, .article-card a.read-more').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('blog_card_click', { event_category: 'engagement' });
            });
        });

        var quoteForm = document.getElementById('quoteForm');
        if (quoteForm) {
            quoteForm.addEventListener('submit', function () {
                trackEvent('quote_form_submit', { event_category: 'lead' });
            });
        }

        var params = new URLSearchParams(window.location.search);
        if (params.get('submitted') === 'true') {
            trackLeadSuccess();
        }

        var blogSearch = document.getElementById('blogSearch');
        if (blogSearch) {
            var searchTimer;
            blogSearch.addEventListener('input', function () {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function () {
                    if (blogSearch.value.trim()) {
                        /* Do not send search text — it may contain names or phone numbers. */
                        trackEvent('blog_search', {
                            event_category: 'engagement',
                            has_query: true,
                            query_len: blogSearch.value.trim().length,
                        });
                    }
                }, 800);
            });
        }
    });
})();
