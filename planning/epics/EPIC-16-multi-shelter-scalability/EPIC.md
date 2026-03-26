---
epic_id: EPIC-16
epic_title: Multi-Shelter & Scalability
epic_status: planned
created_date: 2026-03-26
last_updated: 2026-03-26
epic_owner: Platform Engineering
target_release: FPUNA-2026 Wave 3
priority: high
estimated_effort: 35 story points
---

# EPIC-16: Multi-Shelter & Scalability

## Overview

This epic extends the Refugio Animal Paraguay platform from a single-shelter system to a multi-location network supporting multiple shelters across Paraguay. The system enables centralized management of animals, adopters, and donations across locations while maintaining location-specific staff, inventory, and operational data. Core features include shared animal database with location tags, inter-shelter animal transfers, location-specific staff management, and consolidated reporting with location-level drill-down.

A key requirement for Paraguayan context: the system must handle transfer logistics (animals moving between shelters), coordinate medical records across locations, and manage inventory (supplies, medicines) at each facility. The platform enables the Dutch owner to scale operations beyond the primary shelter while maintaining centralized financial control and reporting for EU donors.

## Why This Epic Matters

The Dutch owner's long-term vision includes expanding to multiple shelter locations across Paraguay. Without architectural support for multi-shelter operations, the current system would require duplicate deployments and manual coordination of shared data (animals, donors, medical records). This would create operational friction, data inconsistency, and make it impossible to present donors with consolidated impact reporting across the organization.

Regulatory context: Paraguayan animal welfare licensing may eventually require centralized records for multi-location operations. A scalable, unified platform enables compliance and positions the organization competitively for government partnerships or funding.

From a donor perspective, EU funders supporting "Refugio Animal Paraguay" expect to see impact across the entire organization, not isolated statistics per location. Multi-shelter support is a prerequisite for positioning the organization as a national-scale impact player.

## Target Users

**Central Operations Manager**: Oversees all locations, makes policy decisions, views consolidated metrics.

**Location Managers**: Manage day-to-day operations for their specific shelter, view location-specific data, coordinate with other locations for transfers.

**Adopters**: Find animals across all locations, travel to preferred shelter for pickup.

**Volunteers**: May work at multiple locations, need visibility into their hours/assignments across all sites.

**Donors**: See impact across the entire network, not per-location.

**Veterinarians**: Travel between locations, need access to complete medical records for animals across the network.

## Scope: In Scope

Multi-location data model with shelter/location entity as first-class concept. Shared animal database where animals have a home location (shelter A) but can be visible to all locations for adoption matching and transfer coordination. Location-specific staff management enabling staff to be assigned to one or more locations with role-based permissions per location.

Inter-shelter transfer workflow including initiation by sending location, medical record hand-off, confirmation by receiving location, and cost tracking (transport, medical hold).

Inventory management per location (supplies, medicines, food) with low-stock alerts and inter-location transfer capability for supplies.

Adoption matching across locations with adopter preferences for location proximity.

Reporting with location dimension enabling drill-down from consolidated organization view to individual shelter metrics.

Financial tracking per location with consolidated P&L and allocation of central costs (headquarters, director salary) across locations.

API design supporting location context in requests (headers or path parameters).

## Scope: Out of Scope

Autonomous location franchising or third-party operator support (organization assumes direct control of all locations). Advanced supply chain optimization or automated inventory reordering. Complex inter-location billing for shared services. Geographic routing optimization for animal transport. Real-time location tracking via GPS for transport vehicles. Multi-language or regional currency variants beyond PYG/EUR. Support for federated networks where partner organizations run their own instances.

## Stories

This epic consists of five major stories. Story S01 implements the multi-location data model and migration strategy for existing single-location data. Story S02 builds the inter-shelter transfer workflow with medical record coordination. Story S03 implements location-specific staff management and permission boundaries. Story S04 develops inventory management per location with transfer capability. Story S05 refactors reporting to support location dimensions and consolidated views.

## Dependencies

This epic depends on core API infrastructure, database stability, and completion of adoption flow (EPIC-02), medical records (EPIC-05), and volunteer management (EPIC-06). Major database migration will be required—downtime must be scheduled carefully. Backup and disaster recovery procedures must be robust given increased data complexity.

## Success Metrics

Multi-location data model is successful when the system reliably tracks animals across locations, location-specific staff can only see their location's data (without additional manual enforcement), and consolidated reports accurately reflect network-wide metrics.

Inter-shelter transfers are successful when transfers complete with zero data loss of medical records, transfer processes take less than 5 minutes of staff time, and animals' location status synchronizes correctly across locations within 1 minute.

Adoption matching is successful when adopters see location in search results, location proximity matches adopters' actual location preferences in at least 75% of adoptions, and transfer-required adoptions (animal at different location) are rare (<10%) by adoption volume.

Location-specific reporting shows zero permission leakage (staff see only assigned locations) and consolidated reporting matches sum of location data within rounding error.

Scalability metrics require that adding a new location (provisioning, initial data setup) takes less than 2 hours, and system performance does not degrade by >5% with each additional location (tested up to 10 locations).

## Risk Factors

**Data consistency risk**: Distributed location data could become inconsistent if synchronization fails. Mitigated by transactional updates, replication verification checks, and periodic reconciliation reports.

**Permission boundary risk**: Staff accessing wrong location data due to authorization bypass. Mitigated by location context in every database query, comprehensive permission testing per location, and audit logging of cross-location access.

**Migration risk**: Converting single-location data to multi-location schema could corrupt existing records. Mitigated by extensive testing in staging, rollback plan, and parallel running of old/new systems during transition.

**Operational overhead**: Managing multiple locations increases operational complexity, recruiting difficulty, and coordination burden. Mitigated by clear location management policies, standard operating procedures per location, and centralized financial controls.

**Network/latency risk**: If locations are far apart or internet connectivity is unreliable, data synchronization could lag. Mitigated by local-first design (each location can operate partially offline), eventual consistency model, and conflict resolution procedures.

**Adoption logistics risk**: Transferring animals between locations requires transport coordination and medical holds—increases complexity and cost. Mitigated by clear transfer policies, volunteer transport coordination, and medical clearance procedures.

## Technical Notes

The location model uses a locations table with id, name, address, phone, hours, capacity, and owner/manager assignment. The animals table gains a home_location_id foreign key but retains visibility across all locations. Queries filter by location context from user's session/token.

Transfer workflow creates a transfer_request with source_location, destination_location, animal_id, reason, and status (pending, confirmed, in_transit, arrived). Medical records are linked directly to the animal, not to a location, ensuring they move with the animal. A transfer audit log tracks movement history for compliance.

Staff permissions use a staff_location_assignment junction table mapping staff to locations with role (e.g., manager, volunteer). API middleware injects location context from the JWT token or request header. Database queries apply WHERE location_id IN (user's_assigned_locations) automatically.

Inventory is tracked per location with an inventory_item table (location_id, item_type, quantity, reorder_level). Low-stock alerts are generated by a background job. Inter-location transfers use inventory_transfer records.

Financial reporting uses a location_id dimension in all transaction tables, enabling both consolidated and location-specific P&L. Central costs are allocated using a cost_allocation table defining percentages per location.

The API uses request headers (X-Shelter-ID) or path patterns (/shelters/{shelter_id}/animals) to communicate location context. Client libraries abstract this from application code.

