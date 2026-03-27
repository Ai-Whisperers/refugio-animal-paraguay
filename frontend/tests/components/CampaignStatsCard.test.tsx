import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CampaignStatsCard from "@/components/campaigns/CampaignStatsCard";

describe("CampaignStatsCard", () => {
  const defaultProps = {
    raisedCents: 50000,
    targetCents: 100000,
    currency: "EUR" as const,
    donationCount: 12,
    progressPercentage: 50,
    daysRemaining: 15,
  };

  it("renders all stat labels", () => {
    render(<CampaignStatsCard {...defaultProps} />);
    expect(screen.getByText("Recaudado")).toBeInTheDocument();
    expect(screen.getByText("Meta")).toBeInTheDocument();
    expect(screen.getByText("Donaciones")).toBeInTheDocument();
    expect(screen.getByText("Progreso")).toBeInTheDocument();
    expect(screen.getByText("Dias restantes")).toBeInTheDocument();
  });

  it("displays donation count", () => {
    render(<CampaignStatsCard {...defaultProps} />);
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("displays progress percentage", () => {
    render(<CampaignStatsCard {...defaultProps} />);
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("displays days remaining", () => {
    render(<CampaignStatsCard {...defaultProps} />);
    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("shows 'Sin fecha limite' when daysRemaining is null", () => {
    render(<CampaignStatsCard {...defaultProps} daysRemaining={null} />);
    expect(screen.getByText("Sin fecha limite")).toBeInTheDocument();
  });

  it("applies green color when progress >= 100", () => {
    const { container } = render(
      <CampaignStatsCard {...defaultProps} progressPercentage={100} />
    );
    // Find the progress percentage element
    const progressEl = container.querySelector(".text-green-600");
    expect(progressEl).toBeInTheDocument();
    expect(progressEl?.textContent).toBe("100%");
  });

  it("shows momentum stat when donationsLast24h is provided", () => {
    render(<CampaignStatsCard {...defaultProps} donationsLast24h={3} />);
    expect(screen.getByText("Ultimas 24h")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("hides momentum stat when donationsLast24h is not provided", () => {
    render(<CampaignStatsCard {...defaultProps} />);
    expect(screen.queryByText("Ultimas 24h")).not.toBeInTheDocument();
  });

  it("handles zero values without crashing", () => {
    render(
      <CampaignStatsCard
        raisedCents={0}
        targetCents={100000}
        currency="EUR"
        donationCount={0}
        progressPercentage={0}
        daysRemaining={0}
      />
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
