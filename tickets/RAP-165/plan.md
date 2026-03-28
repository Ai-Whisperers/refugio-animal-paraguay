# RAP-165 Plan

## Objective
Add an EU-format tax receipt PDF for Dutch/European donors with ANBI tax notice and bilingual fields.

## Acceptance Criteria
- [x] TaxReceiptEUGenerator service generates bilingual (Dutch/Spanish) PDF
- [x] PDF includes ANBI/charity registration info and tax deductibility notice
- [x] New endpoint GET /donations/{id}/tax-receipt-eu (staff only)
- [x] 22 unit tests passing

## Complexity Assessment
**Assessment**: Complex Implementation
