# RAP-118 Plan

## Objective
Generate PDF receipts for individual donations with donation details, shelter info, and tax-relevant data.

## Acceptance Criteria
- [ ] Backend endpoint GET /donations/{id}/receipt returns PDF
- [ ] PDF includes donation amount, currency, date, payment method, donor info
- [ ] PDF includes shelter name and contact info
- [ ] Frontend "Generate Receipt" button on donation history
- [ ] Unit tests for receipt generation service

## Complexity Assessment
**Assessment result**: Complex — new service + endpoint + frontend integration

## Approach
1. Create DonationReceiptGenerator service following contract_service.py pattern
2. Add GET /donations/{id}/receipt endpoint
3. Add receipt download button to donation history pages
4. Write unit tests for receipt generation
