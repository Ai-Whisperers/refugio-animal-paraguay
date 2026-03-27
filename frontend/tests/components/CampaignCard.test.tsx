import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CampaignCard from "@/components/CampaignCard";
import type { CampaignPublic } from "@/types/api";

/** Minimal valid campaign fixture — override per test. */
function makeCampaign(overrides: Partial<CampaignPublic> = {}): CampaignPublic {
  return {
    id: "camp-001",
    title: "Ayuda a los perros sin hogar",
    description: "Campana para alimentar y vacunar a perros en situacion de calle.",
    impact_story: null,
    target_amount_cents: 100000,
    raised_amount_cents: 50000,
    currency: "EUR",
    fund_category: "food",
    status: "active",
    image_url: null,
    deadline: null,
    min_donation_cents: null,
    max_donation_cents: null,
    allow_overfunding: false,
    donation_count: 12,
    progress_percentage: 50,
    ...overrides,
  };
}

describe("CampaignCard", () => {
  it("displays campaign title and description", () => {
    render(<CampaignCard campaign={makeCampaign()} />);
    expect(screen.getByText("Ayuda a los perros sin hogar")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Campana para alimentar y vacunar a perros en situacion de calle."
      )
    ).toBeInTheDocument();
  });

  it("links to the campaign detail page", () => {
    render(<CampaignCard campaign={makeCampaign()} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/donate/campaigns/camp-001");
  });

  it("shows progress percentage when campaign is not completed", () => {
    render(<CampaignCard campaign={makeCampaign({ progress_percentage: 65 })} />);
    expect(screen.getByText("65%")).toBeInTheDocument();
  });

  it('shows "Meta alcanzada" when campaign is completed', () => {
    render(
      <CampaignCard
        campaign={makeCampaign({ status: "completed", progress_percentage: 100 })}
      />
    );
    expect(screen.getByText("Meta alcanzada")).toBeInTheDocument();
  });

  it('shows "Meta alcanzada" when progress_percentage reaches 100', () => {
    render(<CampaignCard campaign={makeCampaign({ progress_percentage: 100 })} />);
    expect(screen.getByText("Meta alcanzada")).toBeInTheDocument();
  });

  it("progress bar width is capped at 100% even if over-funded", () => {
    const { container } = render(
      <CampaignCard campaign={makeCampaign({ progress_percentage: 150 })} />
    );
    const bar = container.querySelector('[style*="width"]') as HTMLElement;
    expect(bar.style.width).toBe("100%");
  });

  it("shows donation count", () => {
    render(<CampaignCard campaign={makeCampaign({ donation_count: 7 })} />);
    expect(screen.getByText(/7\s*donaciones/i)).toBeInTheDocument();
  });

  it('uses "donacion" (singular) for count of 1', () => {
    render(<CampaignCard campaign={makeCampaign({ donation_count: 1 })} />);
    expect(screen.getByText(/1\s*donacion$/i)).toBeInTheDocument();
  });

  it("renders campaign image when image_url is provided", () => {
    render(
      <CampaignCard
        campaign={makeCampaign({ image_url: "https://example.com/camp.jpg" })}
      />
    );
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "https://example.com/camp.jpg");
    expect(img).toHaveAttribute("alt", "Ayuda a los perros sin hogar");
  });

  it("renders icon placeholder when image_url is null", () => {
    const { container } = render(<CampaignCard campaign={makeCampaign()} />);
    expect(container.querySelector("img")).not.toBeInTheDocument();
    // Gradient placeholder div should be present
    expect(container.querySelector(".bg-gradient-to-br")).toBeInTheDocument();
  });

  it("shows deadline when campaign is active and has a deadline", () => {
    render(
      <CampaignCard
        campaign={makeCampaign({ deadline: "2026-12-31T00:00:00Z" })}
      />
    );
    expect(screen.getByText(/hasta/i)).toBeInTheDocument();
  });

  it("does not show deadline when campaign is completed", () => {
    render(
      <CampaignCard
        campaign={makeCampaign({
          status: "completed",
          progress_percentage: 100,
          deadline: "2026-12-31T00:00:00Z",
        })}
      />
    );
    expect(screen.queryByText(/hasta/i)).not.toBeInTheDocument();
  });

  it("handles zero raised amount without crashing", () => {
    render(
      <CampaignCard
        campaign={makeCampaign({
          raised_amount_cents: 0,
          progress_percentage: 0,
          donation_count: 0,
        })}
      />
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
