---
story: S01
epic: EPIC-7
title: Admin Dashboard & Analytics
status: ready
created: 2026-03-25T17:13:26.733714
version: V5
---

# S01: Admin Dashboard & Analytics

## Description

Main admin dashboard with real-time KPIs, analytics charts, and operational metrics for shelter management and decision-making.

## Acceptance Criteria

**Given** an admin logs in
**When** they access the main dashboard
**Then** they see key metrics displayed prominently: animals in shelter, pending adoptions, total volunteers, donations this month

**Given** the dashboard displays metrics
**When** the page loads
**Then** KPI cards show: active animals (by species), adoption applications (pending/approved/rejected), donation total (USD/EUR/PYG), volunteer hours

**Given** an admin views the dashboard
**When** they look at charts
**Then** they see: adoption trends (chart by month), donation trends (chart by month/source), animal health status (pie chart), volunteer participation (bar chart)

**Given** I need real-time updates
**When** I view the dashboard
**Then** KPI numbers refresh every minute to show current state (animals in shelter, pending applications, etc.)

**Given** I want to filter dashboard metrics
**When** I select a date range
**Then** charts and KPIs update to show data for selected period (today, this month, this year, custom range)

**Given** I want to see trends
**When** I view analytics charts
**Then** each chart shows trend data with option to export data as CSV and chart image as PNG

**Given** operational issues need attention
**When** alerts exist (overdue vaccination, unapproved adoption app, etc.)
**Then** alert banner appears at top of dashboard with count and link to issue details

**Given** a user views the dashboard on small screen
**When** layout adapts
**Then** dashboard remains usable on mobile/tablet with scrollable card sections and responsive charts

## Tasks

- T01: Design dashboard layout
- T02: Implement analytics charts
- T03: Add real-time metrics
