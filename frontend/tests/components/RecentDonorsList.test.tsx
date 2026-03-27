import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RecentDonorsList from "@/components/campaigns/RecentDonorsList";
import type { RecentDonorEntry } from "@/types/api";

function makeDonor(overrides: Partial<RecentDonorEntry> = {}): RecentDonorEntry {
  return {
    display_name: "Juan P.",
    amount_cents: 5000,
    currency: "EUR",
    donated_at: "2026-03-20T10:00:00Z",
    is_anonymous: false,
    ...overrides,
  };
}

describe("RecentDonorsList", () => {
  it("shows empty state when no donors", () => {
    render(<RecentDonorsList donors={[]} />);
    expect(screen.getByText("Se el primero en donar")).toBeInTheDocument();
  });

  it("renders donor name and formatted amount", () => {
    render(<RecentDonorsList donors={[makeDonor()]} />);
    expect(screen.getByText("Juan P.")).toBeInTheDocument();
  });

  it("shows 'Anonimo' for anonymous donors", () => {
    render(
      <RecentDonorsList
        donors={[makeDonor({ is_anonymous: true, display_name: "Hidden" })]}
      />
    );
    expect(screen.getByText("Anonimo")).toBeInTheDocument();
    expect(screen.queryByText("Hidden")).not.toBeInTheDocument();
  });

  it("shows '?' avatar for anonymous donors", () => {
    render(
      <RecentDonorsList donors={[makeDonor({ is_anonymous: true })]} />
    );
    expect(screen.getByText("?")).toBeInTheDocument();
  });

  it("shows first letter avatar for named donors", () => {
    render(
      <RecentDonorsList donors={[makeDonor({ display_name: "Maria G." })]} />
    );
    expect(screen.getByText("M")).toBeInTheDocument();
  });

  it("limits visible donors to maxVisible", () => {
    const donors = Array.from({ length: 8 }, (_, i) =>
      makeDonor({ display_name: `Donor ${i}`, donated_at: `2026-03-${20 + i}T10:00:00Z` })
    );
    render(<RecentDonorsList donors={donors} maxVisible={3} />);
    expect(screen.getByText("Donor 0")).toBeInTheDocument();
    expect(screen.getByText("Donor 2")).toBeInTheDocument();
    expect(screen.queryByText("Donor 3")).not.toBeInTheDocument();
  });

  it("renders section heading", () => {
    render(<RecentDonorsList donors={[makeDonor()]} />);
    expect(screen.getByText("Donaciones recientes")).toBeInTheDocument();
  });
});
