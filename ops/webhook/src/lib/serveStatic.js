import { createReadStream, existsSync, statSync } from "node:fs";
import path from "node:path";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".xml": "application/xml",
  ".txt": "text/plain; charset=utf-8",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".map": "application/json",
};

const SKIP_PREFIXES = ["/api/", "/webhook", "/liff/", "/ops/"];

export function shouldServeStatic(pathname) {
  if (SKIP_PREFIXES.some((p) => pathname === p.slice(0, -1) || pathname.startsWith(p))) {
    return false;
  }
  return true;
}

export function serveStaticFile(res, root, pathname) {
  const decoded = decodeURIComponent(pathname.split("?")[0]);
  let rel = decoded === "/" ? "/index.html" : decoded;
  const dest = path.resolve(root, "." + rel);
  const rootAbs = path.resolve(root);
  if (!dest.startsWith(rootAbs + path.sep) && dest !== rootAbs) {
    res.writeHead(403);
    res.end("Forbidden");
    return true;
  }
  let file = dest;
  if (existsSync(file) && statSync(file).isDirectory()) {
    file = path.join(file, "index.html");
  }
  if (!existsSync(file) || !statSync(file).isFile()) {
    return false;
  }
  const ext = path.extname(file).toLowerCase();
  res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
  createReadStream(file).pipe(res);
  return true;
}
