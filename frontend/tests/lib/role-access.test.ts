import { describe, it, expect } from "vitest";
import { hasRoleAccess } from "@/lib/role-access";

describe("hasRoleAccess", () => {
  describe("when no requiredRole is set", () => {
    it("returns true for admin role", () => {
      expect(hasRoleAccess("admin")).toBe(true);
    });

    it("returns true for staff role", () => {
      expect(hasRoleAccess("staff")).toBe(true);
    });

    it("returns true for adopter role", () => {
      expect(hasRoleAccess("adopter")).toBe(true);
    });

    it("returns true for null role", () => {
      expect(hasRoleAccess(null)).toBe(true);
    });

    it("returns true when requiredRole is undefined", () => {
      expect(hasRoleAccess("staff", undefined)).toBe(true);
    });
  });

  describe("when requiredRole is admin", () => {
    it("returns true for admin user", () => {
      expect(hasRoleAccess("admin", "admin")).toBe(true);
    });

    it("returns false for staff user", () => {
      expect(hasRoleAccess("staff", "admin")).toBe(false);
    });

    it("returns false for adopter user", () => {
      expect(hasRoleAccess("adopter", "admin")).toBe(false);
    });

    it("returns false for null user role", () => {
      expect(hasRoleAccess(null, "admin")).toBe(false);
    });
  });

  describe("when requiredRole is staff", () => {
    it("returns true for admin user (higher privilege)", () => {
      expect(hasRoleAccess("admin", "staff")).toBe(true);
    });

    it("returns true for staff user (same privilege)", () => {
      expect(hasRoleAccess("staff", "staff")).toBe(true);
    });

    it("returns false for adopter user (lower privilege)", () => {
      expect(hasRoleAccess("adopter", "staff")).toBe(false);
    });

    it("returns false for null user role", () => {
      expect(hasRoleAccess(null, "staff")).toBe(false);
    });
  });

  describe("when requiredRole is adopter", () => {
    it("returns true for admin user", () => {
      expect(hasRoleAccess("admin", "adopter")).toBe(true);
    });

    it("returns true for staff user", () => {
      expect(hasRoleAccess("staff", "adopter")).toBe(true);
    });

    it("returns true for adopter user", () => {
      expect(hasRoleAccess("adopter", "adopter")).toBe(true);
    });

    it("returns false for null user role", () => {
      expect(hasRoleAccess(null, "adopter")).toBe(false);
    });
  });
});
