const buckets = new Map();

function prune(now, windowMs) {
  for (const [key, hits] of buckets) {
    const next = hits.filter((t) => now - t < windowMs);
    if (next.length) buckets.set(key, next);
    else buckets.delete(key);
  }
}

/**
 * In-process fixed window limiter.
 * Key must be server-derived (IP, phone) — never a client-supplied header alone.
 */
export function hitRateLimit(key, { limit, windowMs }) {
  const now = Date.now();
  if (buckets.size > 5000) prune(now, windowMs);
  const hits = buckets.get(key) || [];
  const recent = hits.filter((t) => now - t < windowMs);
  if (recent.length >= limit) {
    buckets.set(key, recent);
    return { ok: false, retryAfterMs: windowMs - (now - recent[0]) };
  }
  recent.push(now);
  buckets.set(key, recent);
  return { ok: true, remaining: limit - recent.length };
}

export function clientIp(req) {
  const direct = req.socket?.remoteAddress || "";
  const forwarded = String(req.headers["x-forwarded-for"] || "")
    .split(",")[0]
    .trim();
  /* Prefer socket; use forwarded only when the process is behind a known proxy. */
  if (process.env.TRUST_PROXY === "1" && forwarded) return forwarded;
  return direct.replace("::ffff:", "") || forwarded || "unknown";
}

export function resetRateLimits() {
  buckets.clear();
}
