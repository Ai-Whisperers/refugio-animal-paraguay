---
task: T02
story: S03
epic: EPIC-9
title: Setup SSL/TLS
status: ready
priority: medium
created: 2026-03-25T17:13:26.736864
---

# T02: Setup SSL/TLS

## Description

Configure HTTPS for all production and staging endpoints using automated TLS certificate provisioning through Let's Encrypt. All HTTP traffic must be redirected to HTTPS with no exceptions. The configuration must meet GDPR requirements for data-in-transit encryption, enforce a minimum TLS version of 1.2, and support automated certificate renewal so that certificates never expire in production. Traefik serves as the TLS termination proxy in front of the FastAPI application.

## Why TLS Is Non-Negotiable

For this application, HTTPS is not merely best practice — it is a legal and ethical requirement on multiple grounds. GDPR Article 32 requires "appropriate technical measures" to protect personal data, and the European Data Protection Board guidance explicitly identifies encryption in transit as a baseline measure. Donor payment flows involve financial intent data and must use the same transport security standard as financial institutions. Adoption records contain personal information about both humans and animals that must not be observable by network intermediaries.

Beyond compliance, donor trust is operationally critical. The Dutch donor base that the shelter depends on for funding is accustomed to HTTPS-secured donation forms. A browser "Not Secure" warning on the donation page would immediately reduce conversion rates.

## Traefik as TLS Termination Layer

Traefik is the reverse proxy that sits in front of the FastAPI application container. It accepts incoming HTTPS connections on port 443, terminates TLS, and forwards plaintext HTTP to the FastAPI application container on the internal Docker network. Traefik also handles the automatic HTTP-to-HTTPS redirect: any request arriving on port 80 receives a 301 redirect to the HTTPS equivalent URL. The FastAPI application itself never sees unencrypted traffic from real users.

Traefik integrates with Let's Encrypt through the ACME protocol. When Traefik first starts with a domain configured, it automatically requests a certificate from Let's Encrypt, completes the HTTP-01 or TLS-ALPN-01 challenge, and stores the certificate in a JSON file on the host filesystem. Subsequent starts use the stored certificate. Traefik monitors expiration dates and renews certificates automatically when they are within thirty days of expiry. No manual intervention is required for the certificate lifecycle.

The Traefik configuration is stored in a file at the project root named traefik.yml, which is deployed to the application server alongside the Docker Compose configuration. This file specifies the ACME email address (the shelter owner's email), the Let's Encrypt server (production for production, staging for the staging environment to avoid rate limiting), and the certificate store file path.

## TLS Protocol and Cipher Configuration

The minimum TLS version accepted is TLS 1.2. TLS 1.0 and TLS 1.1 are disabled because they have known vulnerabilities (POODLE, BEAST, and related attacks) and are no longer considered acceptable by PCI DSS, GDPR guidance, or modern browser security requirements. TLS 1.3 is preferred and is enabled in Traefik's TLS options configuration. TLS 1.3 provides forward secrecy by default and its handshake is faster than TLS 1.2, which reduces latency for the donation flow.

The cipher suites in use follow Mozilla's modern configuration profile: ECDHE with X25519 or P-256 for key exchange, AES-256-GCM or ChaCha20-Poly1305 for encryption, and SHA-384 for message authentication. Weak cipher suites — including RC4, DES, 3DES, and any export-grade cipher — are explicitly disabled. The Mozilla SSL Configuration Generator is the reference for which cipher suites to specify, using the "Modern" profile.

## HTTP Strict Transport Security

The HTTPS response for all routes includes the Strict-Transport-Security header. The initial deployment sets a max-age of one year (31536000 seconds) and includes the includeSubDomains directive. The preload directive is not added initially — HSTS preloading is a one-way operation that is difficult to reverse, and it is safer to add it after the application has been running on HTTPS for several months without any HTTPS configuration issues.

The effect of the HSTS header is that browsers cache the instruction to use HTTPS for the shelter's domain for one year. Even if an HTTP link to the shelter's domain is clicked, the browser will internally upgrade the request to HTTPS before sending it. This provides protection against SSL stripping attacks on subsequent visits after the first.

The HSTS header is added as a Traefik middleware configuration applied to all routes. This ensures it is present on all responses regardless of which FastAPI endpoint handled the request, without requiring the FastAPI application to manage it.

## Certificate Storage and Renewal Monitoring

Let's Encrypt certificates issued via ACME have a ninety-day validity period. Traefik renews them automatically thirty days before expiry. The certificate data is stored in a file named acme.json on the application server's host filesystem, mounted into the Traefik container as a volume. This file is owned by root with permissions restricted to root-only read/write, because it contains the private key.

The acme.json file must be included in the host-level backup. If the server is replaced and the acme.json file is lost, new certificates will be issued automatically on next startup, but this requires the domain to be resolvable. A backup of acme.json allows the new server to start with valid certificates immediately without waiting for a new ACME challenge.

An external uptime monitoring service (configured in T03 of this story's sibling task on monitoring) is configured to alert on SSL certificate expiry as an independent check. If Traefik's automatic renewal were to fail silently, the monitoring service would alert when the certificate reaches the critical expiry threshold of fourteen days. This belt-and-suspenders approach ensures a certificate expiry incident does not cause a surprise outage.

## GDPR Compliance Notes

The TLS configuration described here satisfies the encryption-in-transit requirement under GDPR Article 32 as interpreted by the EDPB for this application category. The specific compliance evidence to record in the Data Protection Impact Assessment is: TLS 1.2 minimum enforced, TLS 1.3 supported and preferred, modern cipher suites per Mozilla's profile, HSTS enabled with one-year max-age, automated certificate renewal preventing expiry gaps, and the Let's Encrypt CA used is operated by the Internet Security Research Group (ISRG), a US-based non-profit whose certificate authority operations are acceptable under GDPR's standard contractual clauses for data transfer.

A note in docs/compliance/gdpr-tls-evidence.md records the specific TLS configuration choices and the date they were verified, providing an audit trail for any future data protection authority inquiry.

## Testing TLS Configuration

After deployment, the TLS configuration is verified using SSL Labs' server test (or the equivalent testssl.sh tool run locally) and the result should achieve at minimum a grade of A. The test verifies: certificate validity, correct chain, HSTS header presence, TLS 1.2 minimum, no weak ciphers, and that TLS 1.0 and 1.1 are rejected. The test result is saved as a PDF or screenshot to docs/compliance/ with the date of verification.

The HTTP-to-HTTPS redirect is verified manually by making a plain HTTP request to port 80 and confirming a 301 redirect response with the Location header pointing to the HTTPS URL. The HSTS header is verified by inspecting the response headers of an HTTPS request.

Automated tests in the test suite include a smoke test that calls the production health endpoint over HTTPS and asserts a 200 response, confirming that TLS is functioning correctly as part of every post-deployment verification.
