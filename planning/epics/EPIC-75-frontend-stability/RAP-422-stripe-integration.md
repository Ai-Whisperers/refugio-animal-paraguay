---
story: RAP-422
epic: EPIC-75
title: "Integrate Stripe.js Elements into DonationForm"
status: ready
priority: 0
points: 5
created: 2026-03-27
---

# RAP-422: Integrate Stripe.js Elements into DonationForm

## Story

As a **donor**, I want **to enter my card details securely in the DonationForm** so that **I can make a donation**.

## Description

The DonationForm currently calls the backend API but has no Stripe.js Elements to collect card details. Card information must be collected client-side using Stripe Elements, then tokenized before sending to backend.

## Acceptance Criteria

### Install Stripe Libraries

**Given** project setup
**When** dependencies are added
**Then**
- [ ] `@stripe/stripe-js` installed (Stripe.js library)
- [ ] `@stripe/react-stripe-js` installed (React wrapper)
- [ ] Versions are specified in `package.json`

**Commands**:
```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

### Initialize Stripe

**Given** application starts
**When** Stripe is initialized
**Then**
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` env var is set
- [ ] Stripe is initialized with publishable key
- [ ] Stripe context is provided to app

**File: `frontend/src/app/layout.tsx`**:
```typescript
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!
);

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>
        <Elements stripe={stripePromise}>
          {children}
        </Elements>
      </body>
    </html>
  );
}
```

### Add Card Input Field

**Given** DonationForm is rendered
**When** form is displayed
**Then**
- [ ] CardElement is rendered (secure card input)
- [ ] Placeholder text guides user to enter card details
- [ ] Field shows validation errors in real-time

**File: `frontend/src/components/DonationForm.tsx`**:
```typescript
"use client";

import { useState } from "react";
import { CardElement, useStripe, useElements } from "@stripe/react-stripe-js";

export default function DonationForm() {
  const stripe = useStripe();
  const elements = useElements();
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("EUR");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;  // Stripe not loaded
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Create payment intent on backend
      const intentResponse = await fetch("/api/payments/create-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_cents: Math.floor(parseFloat(amount) * 100),
          currency: currency.toLowerCase(),
        }),
      });

      if (!intentResponse.ok) {
        throw new Error("Failed to create payment intent");
      }

      const { clientSecret } = await intentResponse.json();

      // 2. Confirm payment with Stripe.js
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error("Card element not found");
      }

      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            // Optional: add billing details
          },
        },
      });

      if (result.error) {
        setError(result.error.message || "Payment failed");
      } else if (result.paymentIntent?.status === "succeeded") {
        setSuccess(true);
        setAmount("");
        // Clear card element
        cardElement.clear();
        // Show success message
        alert("¡Gracias por su donación!");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An error occurred"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto p-6">
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Monto
        </label>
        <input
          type="number"
          step="0.01"
          min="1"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="100.00"
          className="w-full px-4 py-2 border rounded"
          required
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Moneda
        </label>
        <select
          value={currency}
          onChange={(e) => setCurrency(e.target.value)}
          className="w-full px-4 py-2 border rounded"
        >
          <option value="EUR">EUR (€)</option>
          <option value="PYG">PYG (₲)</option>
          <option value="USD">USD ($)</option>
        </select>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Datos de la tarjeta
        </label>
        <CardElement
          options={{
            style: {
              base: {
                fontSize: "16px",
                color: "#424770",
                "::placeholder": {
                  color: "#aab7c4",
                },
              },
              invalid: {
                color: "#fa755a",
              },
            },
          }}
        />
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded text-green-800">
          ¡Gracias! Su donación fue procesada exitosamente.
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !stripe || !amount}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
      >
        {loading ? "Procesando..." : "Donar"}
      </button>
    </form>
  );
}
```

### Backend Payment Intent Endpoint

**Given** frontend creates payment intent
**When** frontend calls `/api/payments/create-intent`
**Then**
- [ ] Stripe PaymentIntent is created on backend
- [ ] clientSecret is returned to frontend
- [ ] Amount is validated (> 0, reasonable max)

**File: `src/api/payments.py`** (example):
```python
@router.post("/payments/create-intent")
async def create_payment_intent(
    request: CreatePaymentIntentSchema,
    current_user: User,
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=request.amount_cents,
            currency=request.currency,
            metadata={"user_id": str(current_user.id)},
        )
        return {"clientSecret": intent.client_secret}
    except stripe.error.CardError as e:
        raise APIException(
            detail="Invalid payment parameters",
            error_code="INVALID_PAYMENT_PARAMS",
            status_code=400,
        )
```

### Handle Payment Success

**Given** payment is confirmed
**When** `confirmCardPayment` succeeds
**Then**
- [ ] Success message is shown
- [ ] Form is reset
- [ ] Card element is cleared
- [ ] User is redirected or notified

**Pattern** (already in form above):
```typescript
if (result.paymentIntent?.status === "succeeded") {
  setSuccess(true);
  cardElement.clear();
  // Optional: redirect to confirmation page
  // router.push("/donation-confirmed");
}
```

### Handle Payment Errors

**Given** payment fails
**When** error is returned
**Then**
- [ ] Error message is displayed (user-friendly)
- [ ] Error details are NOT exposed (no internal messages)
- [ ] Retry button is available

**Pattern** (already in form above):
```typescript
if (result.error) {
  setError(result.error.message || "Payment failed");
  // Optional: log to Sentry
  Sentry.captureException(new Error(result.error.message));
}
```

### Test with Stripe Test Cards

**Given** form is tested
**When** test cards are used
**Then**
- [ ] Success: 4242 4242 4242 4242
- [ ] Decline: 4000 0000 0000 0002
- [ ] Expired: 4000 0000 0000 0069
- [ ] Form handles each response appropriately

**Stripe test card docs**: https://stripe.com/docs/testing

### Environment Variables

**Given** form is deployed
**When** Stripe is initialized
**Then**
- [ ] Development: test publishable key
- [ ] Production: live publishable key

**File: `.env.local` (development)**:
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**File: Production deploy config**:
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Security Considerations

**Given** card details are collected
**When** form is used
**Then**
- [ ] Card data NEVER touches backend (handled by Stripe client-side)
- [ ] Only clientSecret is sent from backend to frontend
- [ ] Use HTTPS in production
- [ ] No logging of sensitive card data

## Definition of Done

- [ ] Stripe libraries installed
- [ ] Stripe initialized in `frontend/src/app/layout.tsx`
- [ ] DonationForm has CardElement
- [ ] Form submits to create payment intent
- [ ] Payment intent is confirmed with Stripe.js
- [ ] Success message shown on completion
- [ ] Error message shown on failure
- [ ] Form is reset after successful donation
- [ ] Test with Stripe test cards passes
- [ ] Environment variables set correctly
- [ ] Component tests pass (RAP-409)
- [ ] Code review approved

## Technical Notes

### Files to Create/Modify
- `frontend/src/app/layout.tsx` — Initialize Stripe provider
- `frontend/src/components/DonationForm.tsx` — Add CardElement
- `src/api/payments.py` — Create payment intent endpoint
- `.env.local` — Add Stripe publishable key

### Stripe.js v3 API

Stripe.js v3 is latest (v2 is deprecated):
```typescript
import { loadStripe } from "@stripe/stripe-js";
const stripe = await loadStripe("pk_...");
```

### Testing Payment Flow

1. Fill form with amount (e.g., 100)
2. Enter test card: 4242 4242 4242 4242
3. Expiry: any future date
4. CVC: any 3 digits
5. Click Donate
6. Payment should succeed
7. Success message shown

---

*Last updated: 2026-03-27*
