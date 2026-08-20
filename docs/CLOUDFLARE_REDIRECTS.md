# Cloudflare HTTP 301 redirects (GitHub Pages origin)

Site stays on **GitHub Pages**. Cloudflare sits in front and returns real **301**
for cannibalization / editorial soft-redirect URLs from `seo/redirects.json`.

HTML soft redirects remain as a fallback if the Worker is not yet attached.

## Why a Worker

Cloudflare Free **Bulk Redirect Lists** are capped (~25 URLs). This site has
100+ rules, so a Worker with an embedded map fits Free plan better.

## One-time setup

1. Create a Cloudflare account and **Add site** `sangkanclean.com`.
2. At the registrar (currently dns-parking / Hostinger NS), set nameservers to
   the two Cloudflare NS values shown in the dashboard.
3. In DNS, recreate records (proxied / orange cloud):
   - `www` **CNAME** → `pattarish-web.github.io`
   - apex **A** → GitHub Pages IPs (`185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`) — or Cloudflare “Apex CNAME” /
     CNAME flattening to `pattarish-web.github.io` if offered
4. SSL/TLS mode: **Full** (GitHub Pages serves HTTPS).
5. Keep GitHub custom-domain DNS check happy (same targets as today).

## Deploy the Worker

```bash
cd seo/cloudflare
npx wrangler login
npx wrangler deploy
```

Then in Cloudflare → Workers → `sangkanclean-redirects` → **Triggers / Routes**:

- `www.sangkanclean.com/*`
- `sangkanclean.com/*`

## Regenerate after redirect changes

Whenever `seo/redirects.json` changes:

```bash
python seo/generate_cloudflare_redirects.py
cd seo/cloudflare && npx wrangler deploy
```

`build_site.apply_redirect_stubs()` does not deploy Cloudflare; deploy is manual
(or add a CI job with `CLOUDFLARE_API_TOKEN` when ready).

## Verify

```bash
curl -sI "https://www.sangkanclean.com/blog/<stub-slug>.html" | head
# Expect: HTTP/2 301  and  Location: https://www.sangkanclean.com/blog/<winner>.html
```

Apex should 301 to `www`:

```bash
curl -sI "https://sangkanclean.com/" | head
```
