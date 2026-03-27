---
story: S4
epic: EPIC-89
ticket: RAP-607
title: "Campaign-specific financial reports"
status: ready
points: 5
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S04: Per-Campaign Financial Report

## Story

As a campaign owner, I want to see exactly how much was donated to my campaign and where that money was spent so that I can provide accountability to campaign supporters.

## Description

Add financial report section to campaign detail page showing amount raised, amount spent on campaign, remaining balance, and expense breakdown by category. Implement expense allocation workflow allowing admins to link expenses to campaigns.

## Acceptance Criteria

- [ ] Modify /campaigns/{id} page to include "Financial Report" section
- [ ] Report shows:
  - [ ] Amount raised: total donations to this campaign
  - [ ] Amount spent: sum of linked approved expenses
  - [ ] Remaining balance: raised - spent (balance in PYG/USD)
  - [ ] Expense breakdown: pie chart by category
- [ ] Create /admin/expenses/{id}/allocate endpoint
- [ ] Allow admin to link multiple expenses to single campaign via POST
- [ ] Expenses can be allocated to multiple campaigns (split allocation)
- [ ] Show allocated percentage if partially allocated
- [ ] Campaign detail shows list of linked expenses
- [ ] Expense allocation UI: admin can pick campaign from dropdown when creating/editing expense
- [ ] Support multiple campaign allocation: "Allocate to campaigns: [X] [Y] [Z]"
- [ ] Show allocation summary: "50% Campaign A, 50% Campaign B"
- [ ] Financial report queries use approved expenses only
- [ ] Campaign report updates in real-time when expenses approved/allocated
- [ ] Display allocation history: created_at, amount allocated, allocated_by user
- [ ] Responsive layout on mobile and desktop

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Allocation API endpoint implemented and tested
- [ ] Campaign detail page updated with financial section
- [ ] Charts display correctly with allocated expenses
- [ ] Admin allocation UI tested
- [ ] Data accuracy verified: allocations sum correctly
- [ ] Unit tests for allocation calculations
- [ ] Integration test for expense allocation workflow
- [ ] Manual testing of full workflow
- [ ] Mobile responsive layout verified
- [ ] Query performance verified for large campaigns
- [ ] Deployed to staging and verified

## Technical Notes

- Create CampaignExpense join table (campaign_id, expense_id, allocation_percentage)
- Ensure allocation percentages sum to 100% per expense
- Implement cascade delete for allocations when expense deleted
- Use database constraints to enforce data integrity
- Cache campaign financial summary
- Optimize queries with proper joins
- Show unallocated expenses separately

## Story Points: 5
