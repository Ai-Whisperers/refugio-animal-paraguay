# Backend API Endpoint Examples

Quick reference for testing the API with curl or Postman.

## Authentication

### Login
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=securepassword"
```

**Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Account Locked (423)**:
```json
{
  "error_code": "ACCOUNT_LOCKED",
  "message": "Account temporarily locked due to too many failed login attempts. Try again in 15 minute(s).",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Create User (Admin Only)
```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff@example.com",
    "password": "SecurePass123!",
    "role": "staff"
  }'
```

**Success (201)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "staff@example.com",
  "role": "staff",
  "email_verified": false,
  "is_active": true
}
```

### Get Current User
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Animals

### List Animals
```bash
# All animals
curl http://localhost:8000/animals

# Filter by species
curl "http://localhost:8000/animals?species=dog"

# Filter by status
curl "http://localhost:8000/animals?status=available"

# Paginated
curl "http://localhost:8000/animals?offset=0&limit=20"
```

**Response (200)**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Buddy",
    "species": "dog",
    "status": "available",
    "breed": "Golden Retriever",
    "size": "large",
    "gender": "male",
    "birth_date": "2021-05-15",
    "description": "Friendly and energetic",
    "primary_photo_url": "https://example.com/buddy.jpg",
    "photos": [
      {
        "id": "234e4567-e89b-12d3-a456-426614174001",
        "url": "https://example.com/buddy-2.jpg",
        "caption": "Playing fetch",
        "display_order": 1
      }
    ],
    "created_at": "2026-03-20T10:30:00Z",
    "updated_at": "2026-03-20T10:30:00Z"
  }
]
```

### Create Animal (Staff Only)
```bash
curl -X POST http://localhost:8000/animals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Max",
    "species": "cat",
    "status": "available",
    "breed": "Siamese",
    "size": "small",
    "gender": "female",
    "birth_date": "2023-01-10",
    "description": "Shy but loving",
    "primary_photo_url": "https://example.com/max.jpg"
  }'
```

---

## Donations

### Create Donation (Public)
```bash
curl -X POST http://localhost:8000/donations \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": null,
    "amount_cents": 10000,
    "currency": "EUR",
    "payment_method": "stripe",
    "fund_category": "medical",
    "campaign_id": null,
    "is_recurring": false,
    "notes": "In honor of Buddy"
  }'
```

**Response (201)**:
```json
{
  "id": "345e4567-e89b-12d3-a456-426614174001",
  "donor_id": null,
  "amount_cents": 10000,
  "currency": "EUR",
  "payment_method": "stripe",
  "status": "pending",
  "fund_category": "medical",
  "is_recurring": false,
  "stripe_payment_intent_id": null,
  "receipt_number": null,
  "notes": "In honor of Buddy",
  "created_at": "2026-03-27T14:30:00Z",
  "updated_at": "2026-03-27T14:30:00Z"
}
```

### Create Stripe Payment Intent
```bash
curl -X POST http://localhost:8000/donations/345e4567-e89b-12d3-a456-426614174001/stripe-intent \
  -H "Content-Type: application/json"
```

**Response (200)**:
```json
{
  "client_secret": "pi_3LwJx2IJDe5F7qsC0v7xW9I8_secret_7m8xC0kL9xW2J5q3R4s",
  "payment_intent_id": "pi_3LwJx2IJDe5F7qsC0v7xW9I8"
}
```

### Record Cash Donation (Staff Only)
```bash
curl -X POST http://localhost:8000/donations/cash \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": "123e4567-e89b-12d3-a456-426614174123",
    "amount_cents": 25000,
    "currency": "EUR",
    "notes": "Cash donation received at event"
  }'
```

### Get Donation Stats (Staff Only)
```bash
curl http://localhost:8000/donations/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Response (200)**:
```json
{
  "total_donations": 45,
  "total_amount_cents": 125000,
  "total_amount_formatted": "€1,250.00",
  "status_breakdown": {
    "pending": 5,
    "completed": 38,
    "failed": 2
  },
  "currency_breakdown": [
    {
      "currency": "EUR",
      "count": 40,
      "total_cents": 100000
    },
    {
      "currency": "USD",
      "count": 5,
      "total_cents": 25000
    }
  ],
  "payment_method_breakdown": [
    {
      "payment_method": "stripe",
      "count": 30,
      "total_cents": 90000
    },
    {
      "payment_method": "cash",
      "count": 10,
      "total_cents": 35000
    }
  ]
}
```

---

## Adoption Requests

### Create Adoption Request (Staff Only)
```bash
curl -X POST http://localhost:8000/adoption-requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "animal_id": "123e4567-e89b-12d3-a456-426614174001",
    "adopter_id": "456e4567-e89b-12d3-a456-426614174001",
    "notes": "Family approved for large dogs"
  }'
```

**Response (201)**:
```json
{
  "id": "567e4567-e89b-12d3-a456-426614174001",
  "animal_id": "123e4567-e89b-12d3-a456-426614174001",
  "adopter_id": "456e4567-e89b-12d3-a456-426614174001",
  "status": "pending",
  "submitted_at": "2026-03-27T14:30:00Z",
  "decided_at": null,
  "notes": "Family approved for large dogs"
}
```

### Get Adoption Analytics (Staff Only)
```bash
curl http://localhost:8000/adoption-requests/analytics \
  -H "Authorization: Bearer $TOKEN"
```

**Response (200)**:
```json
{
  "total_requests": 42,
  "status_breakdown": {
    "pending": 8,
    "approved": 28,
    "rejected": 5,
    "cancelled": 1
  },
  "avg_time_to_decision_hours": 48.5,
  "approval_rate_percent": 84.8,
  "requests_last_7_days": 6,
  "requests_last_30_days": 18
}
```

### Update Adoption Status (Staff Only)
```bash
curl -X PATCH http://localhost:8000/adoption-requests/567e4567-e89b-12d3-a456-426614174001/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "notes": "Interview passed all checks"
  }'
```

**Response (200)**:
```json
{
  "id": "567e4567-e89b-12d3-a456-426614174001",
  "status": "approved",
  "decided_at": "2026-03-27T15:00:00Z",
  "notes": "Interview passed all checks"
}
```

---

## Public APIs

### Public List Animals
```bash
curl http://localhost:8000/public/animals
```

### Submit Adoption Application (Public)
```bash
curl -X POST http://localhost:8000/public/adoption-applications \
  -H "Content-Type: application/json" \
  -d '{
    "animal_id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+595961234567",
    "message": "We are very interested in adopting Buddy",
    "gdpr_consent": true
  }'
```

**Response (201)**:
```json
{
  "id": "678e4567-e89b-12d3-a456-426614174001",
  "animal_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "pending",
  "submitted_at": "2026-03-27T16:00:00Z"
}
```

**Rate Limited (429)**:
```json
{
  "error_code": "RATE_LIMITED",
  "message": "Rate limit exceeded. Please retry later.",
  "request_id": "789e4567-e89b-12d3-a456-426614174001"
}
```

### Submit Contact Form (Public)
```bash
curl -X POST http://localhost:8000/public/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "subject": "Question about volunteering",
    "message": "I would like to volunteer at the shelter"
  }'
```

---

## Sponsorships

### Get Sponsorship Tiers (Public)
```bash
curl http://localhost:8000/sponsorships/tiers
```

**Response (200)**:
```json
[
  {
    "id": "tier-1",
    "name": "Friend",
    "amount_cents": 1000,
    "amount_formatted": "€10.00",
    "description": "Monthly supporter",
    "benefits": ["Monthly updates", "Receipt"]
  },
  {
    "id": "tier-2",
    "name": "Guardian",
    "amount_cents": 5000,
    "amount_formatted": "€50.00",
    "description": "Premium sponsor",
    "benefits": ["Weekly updates", "Photos", "Video calls", "Receipt"]
  }
]
```

### Create Sponsorship (Public)
```bash
curl -X POST http://localhost:8000/sponsorships \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": null,
    "animal_id": "123e4567-e89b-12d3-a456-426614174001",
    "tier_id": "tier-1",
    "amount_cents": 1000,
    "currency": "EUR",
    "payment_method": "stripe",
    "gdpr_consent": true
  }'
```

---

## Medical Records (Vet Only)

### List Vaccinations for Animal (Vet/Staff)
```bash
curl http://localhost:8000/animals/123e4567-e89b-12d3-a456-426614174001/vaccinations \
  -H "Authorization: Bearer $VET_TOKEN"
```

### Record Vaccination (Vet Only)
```bash
curl -X POST http://localhost:8000/animals/123e4567-e89b-12d3-a456-426614174001/vaccinations \
  -H "Authorization: Bearer $VET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vaccine_type": "rabies",
    "vaccination_date": "2026-03-20",
    "next_due_date": "2027-03-20",
    "notes": "Injected in left hindleg"
  }'
```

---

## Admin

### Get Audit Logs (Staff Only)
```bash
curl http://localhost:8000/admin/audit-logs \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

**Response (200)**:
```json
[
  {
    "id": "789e4567-e89b-12d3-a456-426614174001",
    "user_id": "123e4567-e89b-12d3-a456-426614174005",
    "action": "create",
    "resource_type": "animal",
    "resource_id": "123e4567-e89b-12d3-a456-426614174001",
    "changes_before": null,
    "changes_after": {
      "name": "Buddy",
      "species": "dog",
      "status": "available"
    },
    "ip_address": "192.168.1.100",
    "timestamp": "2026-03-27T14:30:00Z"
  }
]
```

---

## Error Responses

### Validation Error (422)
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format",
      "type": "value_error.email"
    }
  ],
  "request_id": "890e4567-e89b-12d3-a456-426614174001"
}
```

### Conflict Error (409)
```json
{
  "error_code": "CONFLICT",
  "message": "A user with this email already exists",
  "request_id": "901e4567-e89b-12d3-a456-426614174001"
}
```

### Not Found (404)
```json
{
  "error_code": "NOT_FOUND",
  "message": "Animal not found",
  "request_id": "012e4567-e89b-12d3-a456-426614174001"
}
```

### Unauthorized (401)
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Invalid or expired token",
  "request_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

### Forbidden (403)
```json
{
  "error_code": "FORBIDDEN",
  "message": "Staff access required",
  "request_id": "234e4567-e89b-12d3-a456-426614174001"
}
```

### Payment Error (402)
```json
{
  "error_code": "CARD_DECLINED",
  "message": "Your card was declined. Please try another card.",
  "request_id": "345e4567-e89b-12d3-a456-426614174001"
}
```

### Internal Server Error (500)
```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "request_id": "456e4567-e89b-12d3-a456-426614174001"
}
```

---

## Testing Workflow

### 1. Create Admin User
```bash
# Assuming default DB has no users yet, or use existing admin

curl -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.local",
    "password": "AdminPass123!",
    "role": "admin"
  }'
```

### 2. Verify Email (Manually for now)
```sql
UPDATE users SET email_verified = true WHERE email = 'admin@test.local';
```

### 3. Login
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.local&password=AdminPass123!"
```

Store token:
```bash
TOKEN="<access_token from response>"
```

### 4. Create Animal
```bash
curl -X POST http://localhost:8000/animals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Buddy",
    "species": "dog",
    "status": "available",
    "breed": "Golden Retriever"
  }'
```

Store animal ID:
```bash
ANIMAL_ID="<id from response>"
```

### 5. Create Adopter
```bash
curl -X POST http://localhost:8000/adopters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+595961234567",
    "address": "123 Main St"
  }'
```

Store adopter ID:
```bash
ADOPTER_ID="<id from response>"
```

### 6. Create Adoption Request
```bash
curl -X POST http://localhost:8000/adoption-requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"animal_id\": \"$ANIMAL_ID\",
    \"adopter_id\": \"$ADOPTER_ID\",
    \"notes\": \"Family approved\"
  }"
```

### 7. Approve Adoption
```bash
REQUEST_ID="<id from previous response>"

curl -X PATCH http://localhost:8000/adoption-requests/$REQUEST_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved"
  }'
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- UUIDs are v4 random
- Amounts in API are always in cents (100 = €1.00)
- Emails are case-insensitive in DB but stored as-provided
- Phone numbers should be E.164 format when provided
- Authentication uses JWT in `Authorization: Bearer` header
- Rate limits apply per IP address (can be overridden in tests)

