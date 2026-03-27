---
epic: EPIC-89
title: "Financial Transparency & Impact Reporting"
status: ready
sprint: 14
points: 38
created: 2026-03-27
version: V14
---
# EPIC-89: Financial Transparency & Impact Reporting

## Overview

This epic implements comprehensive financial transparency and impact reporting features that enable donors to understand exactly how their contributions are being used. The system tracks all expenses, allocates them to campaigns and initiatives, generates financial dashboards, and provides personalized donor impact summaries showing the real-world outcomes of their donations.

Features include expense recording with receipt uploads, public financial dashboards showing income vs expenses, per-campaign financial reports, personalized donor impact summaries, automated monthly impact emails, annual financial reports, and approval workflows for expense authorization.

## Why This Epic Matters

Financial transparency is critical for a nonprofit animal rescue organization. Donors need to see exactly how their money is being used, what impact it has created, and whether the organization is operating efficiently. Lack of transparency erodes trust and reduces donor retention. By providing detailed financial information and personalized impact reports, Refugio Animal Paraguay can build donor confidence, demonstrate accountability, and increase recurring donations.

Many donors are motivated by knowing specific outcomes: "Your donation fed 50 animals for a month" or "Your contribution enabled 3 emergency rescues." By tracking expenses against outcomes, the organization can provide compelling impact stories that increase donor satisfaction and lifetime value.

## Target Users

The financial system serves three user groups: donors who want to understand their impact, staff who need to record expenses and track budgets, and administrators who oversee financial integrity and generate regulatory reports. Each group needs different views of financial data.

## Scope: In Scope

This epic includes expense recording with categories, receipt uploads, and approval workflows. Public financial dashboards showing monthly and annual income, expenses by category, balance, and trends. Per-campaign financial reports linking expenses to campaigns. Personalized donor impact summaries showing how donations were allocated. Automated monthly impact emails for all donors. Annual financial report generation in PDF and CSV formats. Expense approval workflows with notification system.

## Scope: Out of Scope

Integration with accounting software (QuickBooks, etc.) is deferred. Payroll and employee salary tracking are out of scope. Tax documentation generation is not included. Grant tracking and reporting for grant funders is deferred. Cryptocurrency payment tracking is out of scope. Multi-currency accounting complexity beyond basic storage is deferred.

## Stories

This epic consists of 8 stories: S1 implements expense recording system, S2 creates expense recording UI with receipts, S3 builds public financial dashboard, S4 adds per-campaign financial reports, S5 implements donor impact summaries, S6 automates monthly impact emails, S7 generates annual financial reports, and S8 implements expense approval workflow.

## Dependencies

The implementation depends on a working database with campaigns and donations already recorded. The authentication and authorization system must be in place. Image upload infrastructure must exist for receipt handling. Email service must be configured for impact email delivery. PDF generation capability may be needed for reports.

## Success Metrics

Financial tracking succeeds when all expenses are properly categorized and recorded, receipts are accessible, and donation allocations are accurate. Public dashboards succeed when they display current data and update daily. Donor reports succeed when 80% of report recipients open impact emails and 30% are moved to make additional donations. Financial reports succeed when they pass audit trails and satisfy nonprofit accounting standards.

## Risk Factors

The primary risk involves financial data accuracy and audit compliance. If expenses are miscategorized or donations misallocated, it could trigger donor complaints and regulatory issues. This is mitigated through approval workflows, receipt requirements, and regular audits. Data privacy is another risk; financial reports must not expose sensitive donor information. This is mitigated through careful access control and data masking.

## Technical Notes

Financial data is stored in PostgreSQL with proper foreign key relationships. Expenses link to campaigns and funding sources. Donor reports are generated on-demand and cached. Financial summaries are computed nightly as batch jobs. Public dashboards cache data and update daily. Annual reports generate via PDF library or similar.
