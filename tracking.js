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
                fireAdsConversion('phone', { event_category: 'lead', method: 'phone' });
                trackEvent('generate_lead', {
                    method: 'phone',
                    currency: 'THB',
                    event_category: 'lead',
                });
            });
        });

        document.querySelectorAll('a[href*="line.me"]').forEach(function (el) {
            if (el.dataset.adsLineBound) return;
            el.dataset.adsLineBound = '1';
            el.addEventListener('click', function () {
                fireAdsConversion('line', { event_category: 'lead', method: 'line' });
                trackEvent('generate_lead', {
                    method: 'line',
                    currency: 'THB',
                    event_category: 'lead',
                });
            });
        });
    }

    function trackLeadSuccess() {
        var key = 'sc_lead_' + pagePath() + '_' + (window.location.search || '');
        try {
            if (sessionStorage.getItem(key) === '1') return;
            sessionStorage.setItem(key, '1');
        } catch (e) { /* private mode */ }

        trackEvent('quote_form_success', { event_category: 'lead' });
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
                        trackEvent('blog_search', {
                            event_category: 'engagement',
                            search_term: blogSearch.value.trim(),
                        });
                    }
                }, 800);
            });
        }
    });
})();
