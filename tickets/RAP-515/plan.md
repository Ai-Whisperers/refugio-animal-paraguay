# RAP-515 Plan

## Objective
Build admin-only financial reconciliation API endpoints for the veterinary voucher program.

## Description
Admin needs visibility into voucher financial data: total vouchers by status, amounts owed to clinics, and settlement reports. This ticket covers the backend API; frontend will be a separate story.

## Acceptance Criteria
- [ ] GET /api/admin/vouchers/finance/summary — returns aggregate voucher stats
- [ ] GET /api/admin/vouchers/finance/clinics — returns paginated clinic breakdown with outstanding balances
- [ ] GET /api/admin/vouchers/finance/clinics/{clinic_id} — detailed voucher breakdown per clinic
- [ ] GET /api/admin/vouchers/finance/report — monthly settlement report with optional date range filter
- [ ] CSV export endpoint for settlement reports
- [ ] All endpoints require admin auth
- [ ] Unit tests for service layer calculations
- [ ] Integration tests for API endpoints

## Complexity Assessment
**Track**: Complex Implementation — multiple endpoints, aggregation queries, CSV export

## Approach
1. Create VoucherFinanceService with aggregation methods
2. Create Pydantic schemas for responses
3. Create FastAPI router with admin-only endpoints
4. Write unit tests for calculations
5. Write integration tests for endpoints

## Dependencies
- RAP-512 (clinic redemption — merged)
- VetVoucher model (exists)
- VetClinic model (exists)
