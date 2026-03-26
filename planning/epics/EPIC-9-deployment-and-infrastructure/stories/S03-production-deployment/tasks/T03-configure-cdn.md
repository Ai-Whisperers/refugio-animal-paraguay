---
task: T03
story: S03
epic: EPIC-9
title: Configure CDN
status: ready
priority: medium
created: 2026-03-25T17:13:26.736920
---

# T03: Configure CDN

## Description

Configure Cloudflare as the DNS provider and CDN layer in front of the production application. This covers DNS record management, Cloudflare's proxying behavior for the API, cache-control headers on public endpoints, and a strategy for invalidating cached content at deployment time. The frontend stack is not yet chosen, but this task establishes the CDN foundation that the frontend will eventually build on. For the current backend-only deployment, the primary benefit of Cloudflare is DDoS protection, global anycast routing for reduced donor latency, and the ability to apply security rules at the edge before traffic reaches the application server.

## Why Cloudflare

Cloudflare operates a global network with points of presence in Amsterdam, Frankfurt, Paris, London, and other European cities. For a Dutch donor visiting the donation landing page, their initial DNS lookup and TLS handshake will resolve to a Cloudflare node close to them rather than all the way to the Hetzner server in Germany. While the actual API calls must still reach the origin server in Germany to process donations, connection establishment is faster, and static content can be served from the edge entirely.

Cloudflare's free tier is sufficient for this application's traffic volume and includes: unlimited bandwidth, global DNS, DDoS protection, a Web Application Firewall with the OWASP managed ruleset available on paid tiers, and SSL certificates for the Cloudflare-to-client connection. The Business or Enterprise tiers add features like custom WAF rules and priority support that the shelter does not need initially.

An important architectural note: Cloudflare proxies traffic between the visitor and the origin server. The browser-to-Cloudflare connection uses Cloudflare's TLS certificate. The Cloudflare-to-origin connection uses the Let's Encrypt certificate configured on the Traefik server. Both legs are encrypted. Cloudflare's "Full (strict)" SSL mode verifies that the origin certificate is valid, not just present, which prevents man-in-the-middle attacks on the Cloudflare-to-origin leg.

## DNS Configuration

The domain for the application is managed through Cloudflare's DNS. Three record types are required: an A record for the root domain pointing to the application server's floating IP, an A record for the www subdomain pointing to the same floating IP, and a CNAME for api pointing to the root domain (or directly to the floating IP) for API-specific subdomains if needed in a future multi-service architecture. All three records are configured with Cloudflare's proxy enabled (the orange cloud icon in Cloudflare's dashboard), so that Cloudflare intermediates all traffic and real visitor IP addresses are not directly exposed.

The TTL for DNS records is set to Cloudflare's automatic TTL when proxied, which is effectively one minute. This allows rapid failover if the floating IP needs to be remapped to a different origin server. Unproxied DNS records (those that must not go through Cloudflare, such as the database server) are set with a TTL of 300 seconds.

The mail exchanger records for the shelter's email are also managed in this Cloudflare zone, unproxied, pointing to the email provider's servers. Email configuration is outside the scope of this task but must not be broken when the DNS zone is created.

## Cache-Control Strategy for API Endpoints

The FastAPI application explicitly sets Cache-Control headers on responses to communicate caching intent to Cloudflare and to browsers. The strategy distinguishes between three endpoint categories.

Public, anonymously accessible data that changes infrequently — specifically the animal listing and animal detail endpoints — can be cached by Cloudflare at the edge. These endpoints return Cache-Control headers with a max-age of sixty seconds and s-maxage of three hundred seconds. The s-maxage directive is honored by Cloudflare's shared cache but not by private browser caches. This means Cloudflare caches the animal listing for up to five minutes, serving it without hitting the origin for every visitor, while individual browsers only cache for one minute. When shelter staff update an animal's status (marking it adopted, for example), the relevant Cloudflare cache entries are purged via the deployment cache invalidation mechanism described below.

Authenticated endpoints — any route that requires a JWT token — must never be cached by any intermediary. These endpoints return Cache-Control headers of no-store, ensuring that Cloudflare does not cache them and that browsers do not retain them in their local cache. This is critical for routes that return donor PII or adoption records, where serving a cached response to the wrong authenticated user would be a data breach.

Mutation endpoints (POST, PATCH, DELETE) receive a Cache-Control response of no-store automatically by Cloudflare's behavior for non-GET methods. The FastAPI application still sets this header explicitly as defense-in-depth.

The donation form pages and payment intent creation endpoint are not cached. Payment flows involve user-specific state and real-money transactions; there is no acceptable scenario where a cached payment response is served.

## Cache Invalidation at Deployment

When a new version of the application is deployed, any Cloudflare-cached responses that reference API data or frontend assets must be invalidated so that users receive fresh content. The deployment pipeline (defined in EPIC-9 S02 T03) includes a cache purge step that calls the Cloudflare API to purge all cached content for the shelter's domain. This is a full cache purge, not selective, because the set of changed endpoints is not reliably known at deploy time. The Cloudflare API key used for cache purge operations is stored as a GitHub Actions secret and is scoped to cache purge permissions only — it cannot modify DNS records or other Cloudflare settings.

For the animal listing and animal detail endpoints where staff update records between deployments, a lighter cache invalidation approach is possible but deferred to a future phase: the FastAPI application could call the Cloudflare API directly when an animal record is updated, purging only the specific URL's cache entry. This targeted invalidation avoids the five-minute lag after a staff update while avoiding the full-purge overhead. The full deployment purge is sufficient for the initial launch.

## Geo-Routing and Traffic Policy

Cloudflare's load balancing with geo-steering is not needed at this scale, as the application runs on a single origin server. However, Cloudflare's anycast network still reduces latency for the donor-facing endpoints by serving the DNS lookup and TLS handshake from a nearby Cloudflare node before the request reaches the origin in Germany. No additional configuration is needed for this — it is a default behavior of Cloudflare proxied records.

If the shelter expands operations to Paraguay significantly, a second origin server in a South American region could be added to a Cloudflare load balancer with health checks. Cloudflare would then route staff in Paraguay to the nearer server and route European donors to the German server. This is a future-phase consideration and requires no current configuration.

## Frontend Static Asset Serving

The frontend stack is not yet selected (as noted in CLAUDE.md). When the frontend is chosen and deployed, static assets — JavaScript bundles, CSS files, fonts, images — will be served either through Cloudflare R2 (Cloudflare's object storage) or Backblaze B2. Both integrate with Cloudflare's CDN natively, serving assets from Cloudflare's edge without an origin server round-trip. Asset filenames will include content hashes (for example, main.a3f7b2c1.js) so that files change names when their content changes; this allows them to be served with very long cache TTLs (one year) without stale content concerns.

This task establishes the Cloudflare zone and DNS configuration that the frontend will build on. The specific static asset configuration is deferred to the frontend implementation phase.

## Security Configuration

Cloudflare's proxy provides some baseline security. DDoS protection is automatically enabled for all proxied records. Cloudflare's Bot Fight Mode is enabled to reduce automated abuse of the donation and adoption endpoints.

Cloudflare's Web Application Firewall managed rules are available on the Pro tier and above. For the initial launch, the free tier provides basic protection. The Pro tier WAF with the OWASP Core Rule Set enabled is strongly recommended once the application is handling real donations, because it provides automated protection against common injection attacks and scanning at the edge before traffic reaches the FastAPI application.

The Cloudflare "Under Attack" mode, which adds a JavaScript challenge for all visitors, is available as a break-glass measure if the application comes under targeted attack. It is not enabled by default because it would add friction to the donor experience.
