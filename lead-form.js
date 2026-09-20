/** Quote form → Lead API with FormSubmit fallback. Never sends PII to GA4/Ads. */
(function () {
    var TIMEOUT_MS = 8000;
    var HONEYPOT_NAME = "company_website";

    function apiUrl() {
        if (window.LEAD_API_URL) return String(window.LEAD_API_URL).replace(/\/$/, "");
        try {
            var host = window.location.hostname;
            if (host === "www.sangkanclean.com" || host === "sangkanclean.com") {
                return "https://sangkan-office-ops.onrender.com/api/leads";
            }
        } catch (e) { /* ignore */ }
        return "/api/leads";
    }

    function attribution() {
        try {
            if (window.SangkanAttribution && window.SangkanAttribution.snapshot) {
                return window.SangkanAttribution.snapshot();
            }
        } catch (e) {
            /* ignore */
        }
        return {};
    }

    function fillHidden(form, name, value) {
        var el = form.querySelector('[name="' + name + '"]');
        if (!el) {
            el = document.createElement("input");
            el.type = "hidden";
            el.name = name;
            form.appendChild(el);
        }
        el.value = value == null ? "" : String(value);
    }

    function ensureHoneypot(form) {
        if (form.querySelector('[name="' + HONEYPOT_NAME + '"]')) return;
        var wrap = document.createElement("div");
        wrap.setAttribute("aria-hidden", "true");
        wrap.style.cssText =
            "position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;";
        var input = document.createElement("input");
        input.type = "text";
        input.name = HONEYPOT_NAME;
        input.tabIndex = -1;
        input.autocomplete = "off";
        wrap.appendChild(input);
        form.appendChild(wrap);
    }

    function syncAttributionFields(form) {
        var attr = attribution();
        var keys = [
            "gclid",
            "gbraid",
            "wbraid",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "campaignid",
            "adgroupid",
            "creative",
            "keyword",
            "channel",
            "first_channel",
            "landing_page",
            "referrer",
        ];
        for (var i = 0; i < keys.length; i++) {
            fillHidden(form, "attr_" + keys[i], attr[keys[i]] || "");
        }
    }

    function formPayload(form) {
        var data = new FormData(form);
        var consentEl = form.querySelector('[name="consent"]');
        return {
            name: String(data.get("name") || "").trim(),
            phone: String(data.get("phone") || "").trim(),
            service: String(data.get("service") || "").trim(),
            area: String(data.get("area") || "").trim(),
            message: String(data.get("message") || "").trim(),
            consent: !!(consentEl && consentEl.checked),
            honeypot: String(data.get(HONEYPOT_NAME) || ""),
            attribution: attribution(),
            page_path: location.pathname || "/",
            idempotency_key: form.dataset.leadKey || "",
        };
    }

    function nativeSubmit(form) {
        form.dataset.leadFallback = "1";
        HTMLFormElement.prototype.submit.call(form);
    }

    function successRedirect() {
        var next = new URL(location.href);
        next.searchParams.set("submitted", "true");
        next.hash = "quote";
        location.href = next.toString();
    }

    function bind(form) {
        if (form.dataset.leadBound === "1") return;
        form.dataset.leadBound = "1";
        if (!form.dataset.leadKey) {
            form.dataset.leadKey =
                "web-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
        }
        ensureHoneypot(form);
        syncAttributionFields(form);

        form.addEventListener("submit", function (ev) {
            if (form.dataset.leadFallback === "1") return;
            if (form.dataset.leadSending === "1") {
                ev.preventDefault();
                return;
            }
            syncAttributionFields(form);
            ev.preventDefault();
            form.dataset.leadSending = "1";
            var btn = form.querySelector('[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.dataset.originalText = btn.innerHTML;
                btn.innerHTML = "กำลังส่ง...";
            }

            var ctrl = typeof AbortController === "function" ? new AbortController() : null;
            var timer = setTimeout(function () {
                if (ctrl) ctrl.abort();
            }, TIMEOUT_MS);

            var endpoint = apiUrl();

            fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify(formPayload(form)),
                signal: ctrl ? ctrl.signal : undefined,
            })
                .then(function (res) {
                    if (!res.ok) throw new Error("lead_http_" + res.status);
                    return res.json().catch(function () {
                        return { ok: true };
                    });
                })
                .then(function (body) {
                    clearTimeout(timer);
                    if (body && body.ok === false) throw new Error(body.error || "lead_rejected");
                    successRedirect();
                })
                .catch(function () {
                    clearTimeout(timer);
                    nativeSubmit(form);
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var form = document.getElementById("quoteForm");
        if (form) bind(form);
    });
})();
