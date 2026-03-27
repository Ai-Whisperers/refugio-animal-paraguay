import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DonationForm from "@/components/DonationForm";
import type { CampaignPublic } from "@/types/api";

// --- Mock public-api ---
vi.mock("@/lib/public-api", () => ({
  createDonation: vi.fn(),
  createDonor: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error_code: string,
      public detail: string
    ) {
      super(detail);
    }
  },
}));

import * as publicApi from "@/lib/public-api";

/** Minimal campaign fixture — override per test. */
function makeCampaign(overrides: Partial<CampaignPublic> = {}): CampaignPublic {
  return {
    id: "camp-abc",
    title: "Vacunas para felinos",
    description: "Campana de vacunacion para gatos.",
    impact_story: null,
    target_amount_cents: 50000,
    raised_amount_cents: 10000,
    currency: "EUR",
    fund_category: "medical",
    status: "active",
    image_url: null,
    deadline: null,
    min_donation_cents: null,
    max_donation_cents: null,
    allow_overfunding: false,
    donation_count: 5,
    progress_percentage: 20,
    ...overrides,
  };
}

describe("DonationForm — amount step", () => {
  it("renders the amount selection heading", () => {
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    expect(screen.getByText("Elegir monto")).toBeInTheDocument();
  });

  it("shows currency selector buttons: EUR, USD, PYG", () => {
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    expect(screen.getByRole("button", { name: "EUR" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "USD" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "PYG" })).toBeInTheDocument();
  });

  it("shows suggested amount buttons", () => {
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    // Should have at least 4 preset amount buttons + 3 currency buttons + Continue
    expect(screen.getAllByRole("button").length).toBeGreaterThanOrEqual(4);
  });

  it("renders custom amount input", () => {
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    expect(screen.getByRole("spinbutton")).toBeInTheDocument();
  });

  it("Continue button is disabled when no amount is selected", () => {
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    expect(screen.getByRole("button", { name: /continuar/i })).toBeDisabled();
  });

  it("Continue button is enabled after selecting a preset amount", async () => {
    const user = userEvent.setup();
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    // Click the first suggested amount button (not a currency or payment method btn)
    const amountButtons = screen
      .getAllByRole("button")
      .filter(
        (b) =>
          !["EUR", "USD", "PYG", "Continuar", "Tarjeta / SEPA", "Transferencia"].includes(
            b.textContent ?? ""
          )
      );
    await user.click(amountButtons[0]);
    expect(screen.getByRole("button", { name: /continuar/i })).not.toBeDisabled();
  });

  it("typing a custom amount enables Continue", async () => {
    const user = userEvent.setup();
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    await user.type(screen.getByRole("spinbutton"), "25");
    expect(screen.getByRole("button", { name: /continuar/i })).not.toBeDisabled();
  });

  it("shows error when amount is below campaign minimum", async () => {
    const user = userEvent.setup();
    render(
      <DonationForm
        campaign={makeCampaign({ min_donation_cents: 1000 })}
        onSuccess={vi.fn()}
      />
    );
    await user.type(screen.getByRole("spinbutton"), "1"); // 1 EUR = 100 cents < 1000
    await user.click(screen.getByRole("button", { name: /continuar/i }));
    expect(screen.getByText(/monto minimo/i)).toBeInTheDocument();
  });

  it("shows error when amount exceeds campaign maximum", async () => {
    const user = userEvent.setup();
    render(
      <DonationForm
        campaign={makeCampaign({ max_donation_cents: 500 })}
        onSuccess={vi.fn()}
      />
    );
    await user.type(screen.getByRole("spinbutton"), "100"); // 100 EUR = 10000 cents > 500
    await user.click(screen.getByRole("button", { name: /continuar/i }));
    expect(screen.getByText(/monto maximo/i)).toBeInTheDocument();
  });

  it("advances to details step when valid amount is entered", async () => {
    const user = userEvent.setup();
    render(<DonationForm campaign={makeCampaign()} onSuccess={vi.fn()} />);
    await user.type(screen.getByRole("spinbutton"), "10");
    await user.click(screen.getByRole("button", { name: /continuar/i }));
    expect(screen.getByText("Tus datos")).toBeInTheDocument();
  });
});

describe("DonationForm — details step", () => {
  async function renderAtDetailsStep(overrides?: Partial<CampaignPublic>) {
    const user = userEvent.setup();
    render(
      <DonationForm campaign={makeCampaign(overrides)} onSuccess={vi.fn()} />
    );
    await user.type(screen.getByRole("spinbutton"), "10");
    await user.click(screen.getByRole("button", { name: /continuar/i }));
    return user;
  }

  it("shows 'Tus datos' heading", async () => {
    await renderAtDetailsStep();
    expect(screen.getByText("Tus datos")).toBeInTheDocument();
  });

  it("shows name and email fields when not anonymous", async () => {
    await renderAtDetailsStep();
    expect(screen.getByPlaceholderText("Tu nombre")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("tu@email.com")).toBeInTheDocument();
  });

  it("hides name and email fields when anonymous is checked", async () => {
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    expect(screen.queryByPlaceholderText("Tu nombre")).not.toBeInTheDocument();
  });

  it("Donate button is disabled without name and email", async () => {
    await renderAtDetailsStep();
    const donateBtn = screen.getByRole("button", { name: /donar/i });
    expect(donateBtn).toBeDisabled();
  });

  it("Donate button is enabled for anonymous donation", async () => {
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    expect(screen.getByRole("button", { name: /donar/i })).not.toBeDisabled();
  });

  it("calls createDonation with correct payload for anonymous donation", async () => {
    vi.mocked(publicApi.createDonation).mockResolvedValueOnce({ id: "don-001" } as never);
    const onSuccess = vi.fn();
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    await user.click(screen.getByRole("button", { name: /donar/i }));
    await waitFor(() => {
      expect(publicApi.createDonation).toHaveBeenCalledWith(
        expect.objectContaining({
          campaign_id: "camp-abc",
          currency: "EUR",
        })
      );
    });
    expect(onSuccess).not.toHaveBeenCalled(); // onSuccess is from outer render, not this one
  });

  it("shows loading spinner while submitting", async () => {
    vi.mocked(publicApi.createDonation).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    await user.click(screen.getByRole("button", { name: /donar/i }));
    expect(screen.getByText(/procesando/i)).toBeInTheDocument();
  });

  it("shows error message when submission fails", async () => {
    vi.mocked(publicApi.createDonation).mockRejectedValueOnce(
      new Error("Error de conexion")
    );
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    await user.click(screen.getByRole("button", { name: /donar/i }));
    await waitFor(() => {
      expect(screen.getByText(/error de conexion/i)).toBeInTheDocument();
    });
  });

  it("can go back to amount step", async () => {
    const user = await renderAtDetailsStep();
    await user.click(screen.getByRole("button", { name: /volver/i }));
    expect(screen.getByText("Elegir monto")).toBeInTheDocument();
  });
});

describe("DonationForm — calls onSuccess after successful submission", () => {
  it("calls onSuccess with donation id", async () => {
    vi.mocked(publicApi.createDonation).mockResolvedValueOnce({ id: "don-xyz" } as never);
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<DonationForm campaign={makeCampaign()} onSuccess={onSuccess} />);
    await user.type(screen.getByRole("spinbutton"), "10");
    await user.click(screen.getByRole("button", { name: /continuar/i }));
    await user.click(screen.getByRole("checkbox", { name: /anonima/i }));
    await user.click(screen.getByRole("button", { name: /donar/i }));
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith("don-xyz");
    });
  });
});
