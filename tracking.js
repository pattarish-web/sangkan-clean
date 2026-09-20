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
        return '';
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
