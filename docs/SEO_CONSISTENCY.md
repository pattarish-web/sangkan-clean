# SEO and public AI data maintenance

- `bigcleaning-pricing.json` contains the public Big Cleaning rates. Run `python scripts/sync_bigcleaning_pricing.py` then `python scripts/sync_agent_pricing.py`. Structural changes (minimum, tiers, survey threshold, add-ons) deliberately fail validation until calculators and copy are updated together.
- Marketing calculators require a property type. The exported Next agent UI has no property selector, so its three compiled `createQuote` entry points reject Big Cleaning with the public calculator URL. Other services keep their existing logic. The Next application source is not in this repository: re-run the synchronizer after replacing its export, and migrate this guard into its source when available.
- `agent/api/v1/quotes.json` is a public formula configuration, not a customer quote/lead store. Do not confuse it with private CRM quotation records.
- FAQs are extracted from an explicit FAQ heading/section, or explicit Q/A markup. Generic body headings and appended CTAs are not FAQs. Do not truncate a long heading into a question. Article body H1 becomes H2; the page template owns H1.
- `seo/content_lastmod.json` records known substantive changes. Update the entry only when the corresponding page changes. Article dates use the latest known registry/published/modified date, so upgrade-bot dates are not frozen. Missing dates are omitted rather than fabricated from the build date. Do not touch every sitemap date on a routine build.
- Area pages describe a Service with `areaServed` and refer to the existing business entity; do not represent province center coordinates as branch addresses.
- The unverified `foundingDate: 1993` has been removed. Preserve the distinction between team experience and legal founding date. Add a founding date, named reviewers, customer case studies or branch locations only when supported by real records and publication permission.
- This repair does not claim rankings, Search Console indexing, Google Business Profile consistency, field Core Web Vitals, or AI citation rates have been measured.

Checks:

```text
python -m unittest discover -s tests -v
node tests/verify_agent_pricing.cjs
```

The generated-output tests cover all 313 current sitemap article URLs. A future intentional article addition/removal requires updating that expected count after confirming sitemap coverage.
