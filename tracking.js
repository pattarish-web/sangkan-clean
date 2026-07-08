/** Shared conversion tracking for Sangkan Clean */
(function () {
    window.trackEvent = function (eventName, params) {
        if (typeof gtag === 'function') {
            gtag('event', eventName, params || {});
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('a[href^="tel:"]').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('click_phone', { event_category: 'contact' });
            });
        });

        document.querySelectorAll('a[href*="line.me"]').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('click_line', { event_category: 'contact' });
            });
        });

        document.querySelectorAll('a[href*="m.me"]').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('click_messenger', { event_category: 'contact' });
            });
        });

        document.querySelectorAll('#hero-cta-line, #hero-cta-phone').forEach(function (el) {
            el.addEventListener('click', function () {
                trackEvent('hero_cta_click', { event_category: 'contact', element_id: el.id });
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

        if (window.location.hash === '#quote' && window.location.search.includes('submitted=true')) {
            trackEvent('quote_form_success', { event_category: 'lead' });
        }
        if (new URLSearchParams(window.location.search).get('submitted') === 'true') {
            trackEvent('quote_form_success', { event_category: 'lead' });
        }

        var blogSearch = document.getElementById('blogSearch');
        if (blogSearch) {
            var searchTimer;
            blogSearch.addEventListener('input', function () {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function () {
                    if (blogSearch.value.trim()) {
                        trackEvent('blog_search', { event_category: 'engagement', search_term: blogSearch.value.trim() });
                    }
                }, 800);
            });
        }
    });
})();
