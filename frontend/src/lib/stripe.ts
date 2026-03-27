/**
 * Stripe.js singleton loader.
 *
 * Lazily loads the Stripe.js script via loadStripe() and caches the result
 * so the script is only fetched once per page lifecycle. The publishable key
 * is read from NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY at build/runtime.
 *
 * Usage:
 *   import { stripePromise } from "@/lib/stripe";
 *   <Elements stripe={stripePromise} options={{ clientSecret }}>
 */

import { loadStripe } from "@stripe/stripe-js";
import type { Stripe } from "@stripe/stripe-js";

const STRIPE_PUBLISHABLE_KEY =
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ?? "";

/**
 * Shared Stripe.js promise. Resolves to a Stripe instance (or null if the
 * key is missing / the library fails to load — both treated as no-op by
 * Stripe Elements, which will surface an error to the user).
 */
export const stripePromise: Promise<Stripe | null> = STRIPE_PUBLISHABLE_KEY
  ? loadStripe(STRIPE_PUBLISHABLE_KEY)
  : Promise.resolve(null);
