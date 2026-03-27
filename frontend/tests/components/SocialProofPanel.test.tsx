import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { CampaignSocialProof } from "@/types/api";

// Mock the public API
const mockGetSocialProof = vi.fn();
vi.mock("@/lib/public-api", () => ({
  getCampaignSocialProof: (...args: unknown[]) => mockGetSocialProof(...args),
}));

import SocialProofPanel from "@/components/campaigns/SocialProofPanel";

function makeSocialProof(
  overrides: Partial<CampaignSocialProof> = {}
): CampaignSocialProof {
  return {
    campaign_id: "c-001",
    donor_count: 42,
    total_raised_cents: 250000,
    currency: "EUR",
    progress_percentage: 65,
    donations_last_24_hours: 3,
    donations_last_7_days: 12,
    recent_donors: [
      {
        display_name: "Ana R.",
        amount_cents: 5000,
        currency: "EUR",
        donated_at: "2026-03-20T10:00:00Z",
        is_anonymous: false,
      },
    ],
    ...overrides,
  };
}

describe("SocialProofPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders title and stats after loading", async () => {
    mockGetSocialProof.mockResolvedValueOnce(makeSocialProof());

    render(<SocialProofPanel campaignId="c-001" />);
    expect(
      await screen.findByText("Apoyo de la comunidad")
    ).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("donantes")).toBeInTheDocument();
  });

  it("shows momentum indicator when donations in last 24h", async () => {
    mockGetSocialProof.mockResolvedValueOnce(
      makeSocialProof({ donations_last_24_hours: 5 })
    );

    render(<SocialProofPanel campaignId="c-001" />);
    expect(
      await screen.findByText("5 en las ultimas 24h")
    ).toBeInTheDocument();
  });

  it("hides momentum indicator when no recent donations", async () => {
    mockGetSocialProof.mockResolvedValueOnce(
      makeSocialProof({ donations_last_24_hours: 0 })
    );

    render(<SocialProofPanel campaignId="c-001" />);
    await screen.findByText("Apoyo de la comunidad");
    expect(
      screen.queryByText(/en las ultimas 24h/)
    ).not.toBeInTheDocument();
  });

  it("renders recent donors list", async () => {
    mockGetSocialProof.mockResolvedValueOnce(makeSocialProof());

    render(<SocialProofPanel campaignId="c-001" />);
    expect(await screen.findByText("Ana R.")).toBeInTheDocument();
  });

  it("renders progress bar", async () => {
    mockGetSocialProof.mockResolvedValueOnce(
      makeSocialProof({ progress_percentage: 75 })
    );

    render(<SocialProofPanel campaignId="c-001" />);
    await screen.findByText("Apoyo de la comunidad");
    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "75");
  });

  it("renders nothing on API failure", async () => {
    mockGetSocialProof.mockRejectedValueOnce(new Error("Network error"));

    const { container } = render(<SocialProofPanel campaignId="c-001" />);
    // Wait for loading to finish — panel should disappear
    await vi.waitFor(() => {
      const pulseEl = container.querySelector(".animate-pulse");
      expect(pulseEl).toBeNull();
    });
    expect(
      screen.queryByText("Apoyo de la comunidad")
    ).not.toBeInTheDocument();
  });

  it("shows percentage text", async () => {
    mockGetSocialProof.mockResolvedValueOnce(
      makeSocialProof({ progress_percentage: 88 })
    );

    render(<SocialProofPanel campaignId="c-001" />);
    expect(await screen.findByText("88%")).toBeInTheDocument();
  });
});
