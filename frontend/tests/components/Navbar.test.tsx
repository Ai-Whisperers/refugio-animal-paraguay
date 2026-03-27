import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as nextNavigation from "next/navigation";
import Navbar from "@/components/Navbar";

describe("Navbar", () => {
  beforeEach(() => {
    vi.mocked(nextNavigation.usePathname).mockReturnValue("/");
  });

  it("renders the brand name", () => {
    render(<Navbar />);
    expect(screen.getByText("Refugio Animal")).toBeInTheDocument();
  });

  it("brand name links to home", () => {
    render(<Navbar />);
    const homeLink = screen.getByRole("link", { name: /refugio animal/i });
    expect(homeLink).toHaveAttribute("href", "/");
  });

  it("renders all navigation links in the desktop bar", () => {
    render(<Navbar />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    expect(hrefs).toContain("/animals");
    expect(hrefs).toContain("/donate");
    expect(hrefs).toContain("/contact");
    expect(hrefs).toContain("/about");
  });

  it("shows mobile menu toggle button", () => {
    render(<Navbar />);
    const toggle = screen.getByRole("button", { name: /open menu/i });
    expect(toggle).toBeInTheDocument();
  });

  it("opens mobile menu when toggle is clicked", async () => {
    const user = userEvent.setup();
    render(<Navbar />);
    const toggle = screen.getByRole("button", { name: /open menu/i });
    await user.click(toggle);
    expect(screen.getByRole("navigation", { name: /mobile navigation/i })).toBeInTheDocument();
  });

  it("toggle button label changes to 'Close menu' when menu is open", async () => {
    const user = userEvent.setup();
    render(<Navbar />);
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getByRole("button", { name: /close menu/i })).toBeInTheDocument();
  });

  it("closes mobile menu when toggle is clicked again", async () => {
    const user = userEvent.setup();
    render(<Navbar />);
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    await user.click(screen.getByRole("button", { name: /close menu/i }));
    expect(
      screen.queryByRole("navigation", { name: /mobile navigation/i })
    ).not.toBeInTheDocument();
  });

  it("closes mobile menu when Escape key is pressed", async () => {
    const user = userEvent.setup();
    render(<Navbar />);
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    await user.keyboard("{Escape}");
    expect(
      screen.queryByRole("navigation", { name: /mobile navigation/i })
    ).not.toBeInTheDocument();
  });

  it("highlights the active /animals link", () => {
    vi.mocked(nextNavigation.usePathname).mockReturnValue("/animals");
    render(<Navbar />);
    const animalsLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("href") === "/animals");
    // At least one (desktop) link should have the active class
    expect(animalsLinks.some((l) => l.className.includes("bg-primary-50"))).toBe(true);
  });

  it("does not highlight /animals when on /donate", () => {
    vi.mocked(nextNavigation.usePathname).mockReturnValue("/donate");
    render(<Navbar />);
    const animalsLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("href") === "/animals");
    expect(animalsLinks.every((l) => !l.className.includes("bg-primary-50"))).toBe(true);
  });

  it("highlights the active /donate link when on /donate/campaigns/xxx", () => {
    vi.mocked(nextNavigation.usePathname).mockReturnValue("/donate/campaigns/abc");
    render(<Navbar />);
    const donateLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("href") === "/donate");
    expect(donateLinks.some((l) => l.className.includes("bg-primary-50"))).toBe(true);
  });

  it("mobile menu contains navigation links", async () => {
    const user = userEvent.setup();
    render(<Navbar />);
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    const mobileNav = screen.getByRole("navigation", { name: /mobile navigation/i });
    const mobileLinks = Array.from(mobileNav.querySelectorAll("a")).map((a) =>
      a.getAttribute("href")
    );
    expect(mobileLinks).toContain("/animals");
    expect(mobileLinks).toContain("/donate");
    expect(mobileLinks).toContain("/contact");
  });
});
