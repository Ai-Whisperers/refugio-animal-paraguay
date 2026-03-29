# RAP-211 Plan

## Objective
Enhance the adoption contract PDF system with a `generate_bytes()` method and a download endpoint so staff can retrieve the contract PDF via HTTP streaming.

## Description
The existing `contract_service.py` can generate a contract to disk but has no `generate_bytes()` method. The API returns only a file path — there is no endpoint to actually download the PDF. This story adds streaming download support so generated contracts can be retrieved directly over HTTP.

## Acceptance Criteria
- [ ] `ContractPDFGenerator.generate_bytes()` added — returns `bytes` without filesystem I/O
- [ ] `GET /adoption-requests/{id}/contract/download` endpoint added — streams PDF with `Content-Disposition: attachment`
- [ ] Endpoint enforces staff auth and 404 if request not found
- [ ] Endpoint returns 404 if contract has not been generated yet
- [ ] Unit tests cover `generate_bytes()` happy path and error case
- [ ] Integration test covers download endpoint

## Complexity Assessment
**Track**: Simple Fix — 2 files changed (contract_service.py + adoption_requests.py), well-understood pattern

**Assessment result**: Simple Fix — existing donation_receipt_service uses same generate_bytes pattern

## Approach
1. Add `generate_bytes()` to `ContractPDFGenerator`
2. Add `GET /{request_id}/contract/download` endpoint
3. Write tests

## Dependencies
- Depends on: contract_service.py (already exists), adoption_requests.py (already exists)
- Blocks: nothing

## Risks
- Risk: None — purely additive
