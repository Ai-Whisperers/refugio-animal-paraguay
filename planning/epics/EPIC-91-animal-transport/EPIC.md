---
epic: EPIC-91
title: "Animal Transport & Logistics Network"
status: ready
sprint: 15
points: 29
created: 2026-03-27
version: V15
---
# EPIC-91: Animal Transport & Logistics Network

## Overview

This epic implements a comprehensive transport and logistics network that connects rescuers, adopters, and veterinary clinics with volunteer drivers. The system allows users to request animal transport, matches requests with available drivers based on location and expertise, tracks trips in real-time, and manages driver reimbursement.

## Why This Epic Matters

Animal transport is a critical bottleneck in rescue operations. Injured animals often need immediate transport to veterinary clinics, adopters need transport to pick up animals, and clinic visits require coordination. Without a structured transport system, operations depend on ad-hoc phone calls and volunteer coordination, creating delays and missed opportunities.

By implementing a digital transport network, the organization can dramatically reduce response time, ensure animals reach clinics quickly, and coordinate adoption pickups professionally. The system also provides transparency to all parties and enables fair driver reimbursement.

## Target Users

The transport system serves rescuers requesting urgent transport, adopters requesting pickup assistance, volunteer drivers offering transport services, and veterinary clinics coordinating clinic visits.

## Scope: In Scope

Transport request model with pickup/destination, urgency levels, and status tracking. Volunteer driver registration with vehicle info and coverage areas. Request matching algorithm connecting requests to nearby drivers. Real-time trip tracking with photo evidence on delivery. Vet appointment integration. Driver reimbursement tracking.

## Scope: Out of Scope

GPS real-time tracking (only periodic updates). Advanced routing optimization. Integration with third-party logistics providers. Insurance coverage management. Fuel expense optimization.

## Stories

7 stories: S1 implements transport request model, S2 creates request form, S3 implements driver registration, S4 implements request matching, S5 adds trip tracking, S6 integrates with vet appointments, S7 implements reimbursement tracking.

## Dependencies

Requires authentication system, database, maps API (optional), and notification system.

## Success Metrics

System succeeds when transport requests are fulfilled within 2 hours, 90% of drivers complete deliveries successfully, and drivers report satisfaction with reimbursement process.
