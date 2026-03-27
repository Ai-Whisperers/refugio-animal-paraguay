import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CampaignProgressBar from "@/components/campaigns/CampaignProgressBar";

describe("CampaignProgressBar", () => {
  it("renders with correct aria attributes", () => {
    render(<CampaignProgressBar percentage={50} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("caps width at 100% for over-funded campaigns", () => {
    const { container } = render(
      <CampaignProgressBar percentage={150} animate={false} />
    );
    const bar = container.querySelector('[role="progressbar"]') as HTMLElement;
    expect(bar.style.width).toBe("100%");
  });

  it("uses green color when campaign is completed", () => {
    const { container } = render(
      <CampaignProgressBar percentage={100} isCompleted={true} animate={false} />
    );
    const bar = container.querySelector('[role="progressbar"]') as HTMLElement;
    expect(bar.className).toContain("bg-green-500");
  });

  it("uses primary color when campaign is not completed", () => {
    const { container } = render(
      <CampaignProgressBar percentage={50} isCompleted={false} animate={false} />
    );
    const bar = container.querySelector('[role="progressbar"]') as HTMLElement;
    expect(bar.className).toContain("bg-primary-500");
  });

  it("shows percentage label when showLabel is true", () => {
    render(<CampaignProgressBar percentage={75} showLabel={true} animate={false} />);
    expect(screen.getByText("75% alcanzado")).toBeInTheDocument();
  });

  it("does not show percentage label by default", () => {
    render(<CampaignProgressBar percentage={75} animate={false} />);
    expect(screen.queryByText(/alcanzado/)).not.toBeInTheDocument();
  });

  it("applies custom height class", () => {
    const { container } = render(
      <CampaignProgressBar percentage={50} height="h-4" animate={false} />
    );
    const bar = container.querySelector('[role="progressbar"]') as HTMLElement;
    expect(bar.className).toContain("h-4");
  });

  it("handles 0% without crashing", () => {
    render(<CampaignProgressBar percentage={0} animate={false} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "0");
    expect(bar.style.width).toBe("0%");
  });

  it("rounds percentage for aria label", () => {
    render(<CampaignProgressBar percentage={33.7} animate={false} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-label", "34% alcanzado");
  });
});
