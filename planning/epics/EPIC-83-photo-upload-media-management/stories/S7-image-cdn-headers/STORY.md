---
story: S7
epic: EPIC-83
ticket: RAP-565
title: "Image CDN headers"
status: ready
points: 3
priority: P2
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S7: Image CDN headers

## Story
As a **system**, I want **to optimize image delivery with proper caching and negotiation** so that **pages load quickly and server load is reduced**.

## Description
Configure HTTP caching headers, ETag support, and WebP content negotiation for image serving. Enables browser caching and CDN edge caching for optimal performance.

## Acceptance Criteria
- [ ] Static image serving configured at /media/ path in Nginx
- [ ] Cache-Control header set to "public, max-age=31536000" for optimized images (1 year, assuming UUID filenames are immutable)
- [ ] ETag header generated from file content hash (MD5 or SHA-256), allows 304 Not Modified responses
- [ ] Last-Modified header set to file upload timestamp
- [ ] Content negotiation for WebP: server responds with .webp if Accept header contains "image/webp", falls back to original format
- [ ] Vary header includes "Accept-Encoding" for proper caching of compressed/uncompressed
- [ ] GZIP compression enabled for Nginx static file serving
- [ ] Brotli compression enabled if available (better compression than GZIP)
- [ ] Nginx configuration: gzip on, gzip_types application/json image/svg+xml text/css text/javascript
- [ ] CORS headers if images served from CDN: Access-Control-Allow-Origin: "*"
- [ ] Security headers: X-Content-Type-Options: nosniff (prevents MIME type sniffing)
- [ ] Media files served with Content-Security-Policy restrictions if needed
- [ ] Nginx config tested with ab or wrk load testing tool
- [ ] Cache effectiveness measured: hit rate, bandwidth saved
- [ ] Unit test: verify cache headers in API responses (if serving via API)

## Definition of Done
- [ ] Code complete (Nginx config), peer reviewed
- [ ] Load testing performed and documented
- [ ] Cache effectiveness measured
- [ ] CDN configuration documented
- [ ] Deployed to staging and verified with browser DevTools
- [ ] Real-world performance monitored

## Technical Notes
- Use Nginx configuration: expires 1y (shorthand for cache control)
- Consider CloudFront or similar CDN for geographic distribution
- Monitor cache hit ratio in CDN metrics
- Plan for cache invalidation strategy if image URLs change
- Document content negotiation behavior for developers

## Story Points: 3
