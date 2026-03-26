---
epic_id: EPIC-15
epic_title: Reporting & Business Intelligence
epic_status: planned
created_date: 2026-03-26
last_updated: 2026-03-26
epic_owner: Operations & Finance
target_release: FPUNA-2026 Wave 3
priority: high
estimated_effort: 28 story points
---

# EPIC-15: Reporting & Business Intelligence

## Overview

This epic provides the Refugio Animal Paraguay with comprehensive reporting, analytics, and business intelligence capabilities designed specifically for EU tax compliance, donor management, and operational oversight. The system enables financial reporting across multiple currency denominations (EUR and PYG), generates donor impact statements for European funding networks, tracks operational KPIs relevant to shelter management, and produces exportable reports suitable for regulatory submission.

The platform will deliver dashboards for staff and administrators showing adoption metrics, donation trends, volunteer engagement, and animal welfare outcomes. For donors—especially EU-based supporters—the system generates customized impact reports demonstrating how contributions funded specific programs, medical care, or adoptions. Financial reports will separate EU donations (EUR) from PYG donations and local operating expenses, critical for Dutch owner tax filing and EU donor organization compliance.

## Why This Epic Matters

European funding networks require detailed financial accountability and impact reporting. The Dutch owner must file comprehensive tax reports showing donation flows, operational expenses, and program outcomes for both Dutch corporate tax purposes and EU donor network governance. Without proper reporting infrastructure, the organization cannot effectively manage donor relationships, demonstrate impact to supporters, or maintain compliance with European donor requirements.

Operational reporting is equally critical. Shelter managers need visibility into animal welfare metrics (medical treatment outcomes, adoption success rates), volunteer efficiency, and adoption processing times. Data-driven insights enable continuous improvement, informed decision-making about resource allocation, and evidence-based discussions with the Paraguayan government about animal welfare policy.

For donors—particularly European organizations—customized impact reports showing that "your EUR 500 donation funded emergency surgery for three animals" drive retention and encourage repeat donations. Without this capability, the organization loses opportunities to deepen relationships with its most valuable donor base.

## Target Users

**Shelter Administrators & Finance Manager**: Need financial dashboards showing EUR/PYG balances, expense tracking, monthly reconciliation, and tax-ready reports for filing.

**Volunteer Coordinators & Program Managers**: Need operational dashboards showing adoption processing metrics, volunteer hour tracking, animal census, and medical outcome statistics.

**EU Donors & Donor Organizations**: Receive customized impact reports linking their contributions to specific outcomes (animals saved, medically treated, adopted).

**Dutch Owner & Board**: Quarterly/annual reports for governance, tax compliance, and strategic planning discussions.

**Government & Compliance**: Generate reports for Paraguayan animal welfare authorities and EU organizations if required for certification/licensing.

## Scope: In Scope

Financial reporting covering donation receipt tracking with currency conversion (EUR to PYG), expense categorization by program (medical, operations, adoption), monthly financial summaries with balance sheets, and year-to-date comparisons. Tax-ready export formats (CSV, PDF) suitable for filing with Dutch tax authorities and EU regulatory bodies.

Donor impact reporting including donation history lookup, amount-to-outcome mapping (donations funding specific medical procedures or adoptions), customizable report generation, and scheduled email delivery to donors on annual/quarterly basis.

Operational dashboards displaying adoption metrics (time-to-adoption, success rates, bottleneck identification), volunteer engagement (hours logged, retention trends), animal census (intake/outcome ratios, medical status distribution), and shelter utilization (capacity planning, growth trends).

KPI definitions and tracking including adoption program efficiency, medical cost per animal treated, donor retention rates, volunteer satisfaction proxy metrics, and animal welfare outcome measures.

Exportable reports (PDF, CSV, Excel) for internal analysis, donor communication, board meetings, and regulatory submission.

Dashboard access control ensuring administrators see all metrics, program managers see program-specific data, and donors see only their impact reports.

## Scope: Out of Scope

Real-time predictive analytics or machine learning models for forecasting adoption rates or budget planning are deferred to future phases. Advanced data visualization libraries beyond standard charts/tables. Custom report builder interface—pre-configured templates only. Third-party business intelligence platform integration (Tableau, PowerBI). Multi-organization federation (support for networks of shelter partners) is deferred.

## Stories

This epic consists of seven major stories. Story S01 implements the financial reporting engine with EUR/PYG currency handling and tax-ready exports. Story S02 builds donor impact reporting linking contributions to specific outcomes. Story S03 creates operational dashboards for staff and administrators. Story S04 develops KPI tracking and performance metric calculation. Story S05 implements scheduled report generation and email delivery. Story S06 builds the admin reporting interface for custom filtering and export. Story S07 ensures reporting data security and access control compliance.

## Dependencies

This epic depends on stable completion of the donation system (EPIC-04), animal medical records (EPIC-05), and volunteer management (EPIC-06). Database design must support historical data retention and time-series queries. The API infrastructure must support read-heavy query patterns without performance degradation. Email delivery infrastructure for report distribution must be operational. Currency conversion logic must be robust and tested. Donor management features must be complete to enable impact report generation.

## Success Metrics

Financial reporting is successful when monthly reports reconcile with bank records within PYG 1,000, tax exports are accepted by Dutch tax authority without revision, and EUR/PYG conversion uses consistent, documented exchange rate sources. Donor impact reports are successful when at least 80% of surveyed donors report the impact information is clear and motivating, and adoption of annual reports increases donor retention by measurable percentage.

Operational dashboards are successful when staff adopt metrics within the first month, administrators can identify process bottlenecks within one minute of dashboard access, and adoption processing times decrease by 10% post-implementation due to data-driven process improvements.

Data accuracy metrics require that KPI calculations have zero calculation errors in audit testing, historical data matches source records within 99.95%, and currency conversion variance is under 0.5%.

## Risk Factors

**Data accuracy risk**: Incorrect calculations, missed transactions, or currency conversion errors could produce misleading reports. Mitigated through automated unit testing of all calculation logic, quarterly data audit against source records, and review procedures before reports leave the organization.

**Currency handling risk**: EUR/PYG conversion rate volatility and multiple exchange rate sources could produce inconsistent historical reporting. Mitigated by documenting which exchange rates were used, freezing historical rates (not recalculating retroactively), and using transparent, traceable sources (Central Bank of Paraguay or fixed daily snapshots).

**Donor privacy risk**: Impact reports could inadvertently leak donor giving amounts to other parties. Mitigated by role-based access control, encrypted PDF generation, and clear policies about report distribution.

**Performance risk**: Generating reports on large datasets (millions of transactions) could block normal operations. Mitigated by pre-calculating and caching common reports, background job processing, and database query optimization.

**Compliance risk**: Reports might not satisfy Dutch tax authority or EU donor network requirements on first attempt. Mitigated by consulting with financial advisors early, iterative testing with actual tax filing, and building audit trails into the system.

## Technical Notes

The reporting system uses database views and materialized tables to pre-aggregate data, avoiding expensive calculations at report generation time. Financial data is stored in a transactions table with explicit currency field (EUR or PYG), amount, and timestamp. Donations are linked to specific donation records and animals to enable impact mapping.

Currency conversion uses a snapshot model: a daily conversion rate table captures the official exchange rate on each date, and historical conversions use the rate from the transaction date—not current rates. This prevents confusion from retroactive rate changes and satisfies tax audit requirements.

Donor impact reports use a templating system (Jinja2 or similar) to generate PDF reports with donor name, donation history, and linked outcomes (animals treated, adoptions facilitated). The template system enables customization by text and layout without code changes.

KPIs are calculated using database aggregation queries and cached in a metrics table updated nightly. Dashboard queries read from the cache rather than recalculating, ensuring fast response times.

Access control uses role-based queries: administrator reports include all data, program manager reports filter to their assigned programs, and donor reports use a secure token/session to ensure users see only their own data.

Report exports use CSV for data interchange, PDF for formal documents, and Excel for detailed financial analysis. Exports include metadata (generation date, data period, exchange rates used) to support audit trails.

