---
story: RAP-409
epic: EPIC-72
title: "Add frontend component tests (Jest/Vitest)"
status: ready
priority: 2
points: 2
created: 2026-03-27
---

# RAP-409: Add Frontend Component Tests (Jest/Vitest)

## Story

As a **frontend developer**, I want **component tests for critical UI components** so that **adoption form, donation form, and navigation work correctly**.

## Description

The frontend currently has no component tests. Three critical components need Vitest coverage:

1. `DonationForm.tsx` — Donation amount selection, currency switching, form validation
2. `CampaignCard.tsx` — Campaign display with/without image, progress bar rendering
3. `Navbar.tsx` — Navigation, mobile menu toggle, active route highlighting

## Acceptance Criteria

### DonationForm Component Tests (tests/components/DonationForm.test.tsx)

**Given** a DonationForm component is rendered
**When** user enters donation amount and currency
**Then**
- [ ] Form displays amount input field with default currency (EUR)
- [ ] Currency dropdown shows: EUR, PYG, USD
- [ ] Amount field accepts numeric input
- [ ] Form has "Donate" submit button (disabled if amount ≤ 0)

**Given** user selects 50 EUR
**When** currency is changed to PYG
**Then**
- [ ] Amount is converted using live exchange rate
- [ ] Display shows approximately 50 EUR ≈ X PYG
- [ ] User can override conversion (manual entry)

**Given** user enters invalid amount (negative, zero, non-numeric)
**When** form validation runs
**Then**
- [ ] Error message appears: "Amount must be greater than 0"
- [ ] Submit button is disabled
- [ ] Form does not submit

**Given** user enters valid amount and clicks "Donate"
**When** form is submitted
**Then**
- [ ] API call is made to POST /donations with amount_cents and currency
- [ ] Form shows loading spinner during submission
- [ ] Success message is displayed
- [ ] Form resets for new donation

**Given** API returns error (e.g., 422 Validation Error)
**When** form submission fails
**Then**
- [ ] Error message is displayed to user
- [ ] Form remains populated (user can edit and retry)
- [ ] Retry button is available

**Given** component receives pre-filled props (campaign_id, preset_amount)
**When** component renders
**Then**
- [ ] Amount field is pre-filled if preset_amount provided
- [ ] Currency defaults correctly
- [ ] Campaign name is displayed if campaign_id provided

### CampaignCard Component Tests (tests/components/CampaignCard.test.tsx)

**Given** a CampaignCard component with valid campaign data
**When** component renders
**Then**
- [ ] Campaign name is displayed
- [ ] Campaign description is displayed
- [ ] "Donate" button is visible and clickable
- [ ] Link to campaign details page is present

**Given** campaign has image URL
**When** component renders
**Then**
- [ ] Image is displayed with correct src attribute
- [ ] Image has alt text
- [ ] Image loads without error (mock image service)

**Given** campaign image fails to load (404 or network error)
**When** component handles image error
**Then**
- [ ] Fallback placeholder image is displayed
- [ ] No broken image icon appears
- [ ] Campaign card is still functional

**Given** campaign with fundraising progress (raised/goal)
**When** component renders
**Then**
- [ ] Progress bar is displayed
- [ ] Progress percentage is calculated correctly: (raised / goal) * 100
- [ ] Progress bar fills to correct position
- [ ] Percentage text is shown: "75% funded"

**Given** campaign at 100% or more funding
**When** component renders
**Then**
- [ ] Progress bar shows 100% (not over-filled)
- [ ] Badge "Fully funded" or "Goal exceeded" is displayed
- [ ] "Donate" button is still available (for additional support)

**Given** campaign with 0 raised
**When** component renders
**Then**
- [ ] Progress bar shows 0%
- [ ] "0% funded" or "No donations yet" is displayed
- [ ] Component is not broken

**Given** campaign with missing data (no goal, null image)
**When** component renders
**Then**
- [ ] Component handles gracefully (no crashes)
- [ ] Default/placeholder values are shown
- [ ] Card is still readable and functional

**Given** user clicks on campaign card
**When** click handler is triggered
**Then**
- [ ] Navigation to campaign details page occurs
- [ ] URL is correct: `/campaigns/{campaign_id}`

### Navbar Component Tests (tests/components/Navbar.test.tsx)

**Given** Navbar component renders on desktop
**When** component mounts
**Then**
- [ ] Logo/shelter name is visible
- [ ] Navigation links are displayed: Home, Animals, Donate, Contact, About
- [ ] User menu is visible (if logged in) or Login button (if logged out)
- [ ] Mobile menu toggle is hidden (display: none or not rendered)

**Given** user is not authenticated
**When** Navbar renders
**Then**
- [ ] "Login" button is displayed
- [ ] "Register" button is displayed (if applicable)
- [ ] User menu is not shown

**Given** user is authenticated
**When** Navbar renders
**Then**
- [ ] User menu is displayed with user's name/email
- [ ] "Logout" option is in menu
- [ ] "Profile" or "My Donations" link is in menu
- [ ] Admin menu is shown (if user is admin)

**Given** Navbar is on `/animals` page
**When** component renders
**Then**
- [ ] "Animals" link is highlighted (active state: bold, different color)
- [ ] Other links are not highlighted

**Given** Navbar is on `/donate` page
**When** component renders
**Then**
- [ ] "Donate" link is highlighted
- [ ] Active state matches current route

**Given** Navbar renders on mobile (viewport width < 768px)
**When** component mounts
**Then**
- [ ] Logo/shelter name is visible
- [ ] Desktop navigation links are hidden
- [ ] Mobile menu toggle (hamburger icon) is visible
- [ ] Toggle button is clickable

**Given** mobile menu is closed
**When** hamburger icon is clicked
**Then**
- [ ] Mobile menu slides in (or appears)
- [ ] All navigation links are displayed vertically
- [ ] Toggle icon changes (hamburger → X)
- [ ] Menu can be closed by clicking toggle again

**Given** mobile menu is open and user clicks a link
**When** navigation occurs
**Then**
- [ ] Page navigates to selected link
- [ ] Mobile menu automatically closes
- [ ] Hamburger icon returns to normal state

**Given** user clicks outside mobile menu (on background)
**When** click is on overlay/backdrop
**Then**
- [ ] Mobile menu closes
- [ ] User can interact with page underneath

### Common Component Tests (all components)

**Given** component with dark mode support
**When** theme is toggled
**Then**
- [ ] Component colors update correctly
- [ ] Text remains readable
- [ ] All interactive elements are still visible

**Given** component with accessibility requirements
**When** component renders
**Then**
- [ ] All buttons have accessible labels (aria-label or text)
- [ ] Form inputs have associated labels
- [ ] Images have alt text
- [ ] Interactive elements are keyboard navigable

**Given** component that accepts children
**When** children prop is provided
**Then**
- [ ] Children are rendered
- [ ] Component layout accommodates children

## Definition of Done

- [ ] All test files created and passing
- [ ] Vitest configured in frontend project
- [ ] All tests use Testing Library utilities (render, screen, userEvent)
- [ ] Component coverage ≥ 70% (lower bar for UI)
- [ ] No skipped tests without documented reason
- [ ] All async operations properly handled (waitFor, etc.)
- [ ] Mock API calls using MSW (Mock Service Worker) or jest.mock
- [ ] Code review approved
- [ ] CI pipeline runs tests and reports coverage

## Technical Notes

### Files to Create
- `frontend/tests/components/DonationForm.test.tsx`
- `frontend/tests/components/CampaignCard.test.tsx`
- `frontend/tests/components/Navbar.test.tsx`
- `frontend/vitest.config.ts` (if not exists)
- `frontend/tests/setup.ts` (if not exists)

### Files to Reference
- `frontend/src/components/DonationForm.tsx`
- `frontend/src/components/CampaignCard.tsx`
- `frontend/src/components/Navbar.tsx`
- `frontend/src/lib/public-api.ts` — API utilities to mock

### Setup & Configuration

**Install Vitest dependencies**:
```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D msw # Mock Service Worker for API mocking
npm install -D @vitest/coverage-v8
```

**Create frontend/vitest.config.ts**:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/'],
    },
  },
});
```

**Create frontend/tests/setup.ts**:
```typescript
import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

### Testing Library Patterns

**Render component**:
```typescript
import { render, screen } from '@testing-library/react';
import { DonationForm } from '@/components/DonationForm';

it('renders donation form with amount input', () => {
  render(<DonationForm />);
  const input = screen.getByLabelText(/amount/i);
  expect(input).toBeInTheDocument();
});
```

**User interactions**:
```typescript
import userEvent from '@testing-library/user-event';

it('allows user to enter amount', async () => {
  const user = userEvent.setup();
  render(<DonationForm />);
  const input = screen.getByLabelText(/amount/i);

  await user.type(input, '50');
  expect(input).toHaveValue('50');
});
```

**Async operations**:
```typescript
import { waitFor } from '@testing-library/react';

it('shows success message after submit', async () => {
  const user = userEvent.setup();
  render(<DonationForm />);

  await user.type(screen.getByLabelText(/amount/i), '50');
  await user.click(screen.getByRole('button', { name: /donate/i }));

  await waitFor(() => {
    expect(screen.getByText(/success/i)).toBeInTheDocument();
  });
});
```

**Mocking API calls with MSW**:
```typescript
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.post('*/api/donations', () => {
    return HttpResponse.json({ success: true });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Testing Mobile Responsiveness

```typescript
import { render } from '@testing-library/react';

it('shows mobile menu on small screens', () => {
  // Mock viewport width
  vi.spyOn(window, 'innerWidth', 'get').mockReturnValue(320);

  render(<Navbar />);
  const hamburger = screen.getByRole('button', { name: /menu/i });
  expect(hamburger).toBeInTheDocument();
});
```

---

*Last updated: 2026-03-27*
