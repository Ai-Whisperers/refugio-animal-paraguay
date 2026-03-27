import { describe, it, expect } from "vitest";
import {
  VALID_TRANSITIONS,
  STATUS_LABELS,
  STATUS_COLORS,
  getCommonTransitions,
} from "@/lib/animal-status";
import type { AnimalStatus } from "@/types/api";

const ALL_STATUSES: AnimalStatus[] = [
  "intake",
  "quarantine",
  "available",
  "foster",
  "under_treatment",
  "adopted",
  "deceased",
];

describe("VALID_TRANSITIONS", () => {
  it("defines transitions for all statuses", () => {
    for (const status of ALL_STATUSES) {
      expect(VALID_TRANSITIONS[status]).toBeDefined();
      expect(Array.isArray(VALID_TRANSITIONS[status])).toBe(true);
    }
  });

  it("intake can transition to quarantine, available, under_treatment", () => {
    expect(VALID_TRANSITIONS.intake).toEqual([
      "quarantine",
      "available",
      "under_treatment",
    ]);
  });

  it("available can transition to foster, adopted, under_treatment, quarantine, deceased", () => {
    expect(VALID_TRANSITIONS.available).toEqual([
      "foster",
      "adopted",
      "under_treatment",
      "quarantine",
      "deceased",
    ]);
  });

  it("adopted can only return to available", () => {
    expect(VALID_TRANSITIONS.adopted).toEqual(["available"]);
  });

  it("deceased is a terminal state with no transitions", () => {
    expect(VALID_TRANSITIONS.deceased).toEqual([]);
  });

  it("all transition targets are valid statuses", () => {
    for (const status of ALL_STATUSES) {
      for (const target of VALID_TRANSITIONS[status]) {
        expect(ALL_STATUSES).toContain(target);
      }
    }
  });
});

describe("STATUS_LABELS", () => {
  it("has Spanish labels for all statuses", () => {
    for (const status of ALL_STATUSES) {
      expect(STATUS_LABELS[status]).toBeDefined();
      expect(typeof STATUS_LABELS[status]).toBe("string");
      expect(STATUS_LABELS[status].length).toBeGreaterThan(0);
    }
  });

  it("uses correct Spanish names", () => {
    expect(STATUS_LABELS.intake).toBe("Ingreso");
    expect(STATUS_LABELS.available).toBe("Disponible");
    expect(STATUS_LABELS.adopted).toBe("Adoptado");
    expect(STATUS_LABELS.deceased).toBe("Fallecido");
  });
});

describe("STATUS_COLORS", () => {
  it("has color classes for all statuses", () => {
    for (const status of ALL_STATUSES) {
      expect(STATUS_COLORS[status]).toBeDefined();
      expect(STATUS_COLORS[status]).toContain("bg-");
      expect(STATUS_COLORS[status]).toContain("text-");
    }
  });
});

describe("getCommonTransitions", () => {
  it("returns empty for empty input", () => {
    expect(getCommonTransitions([])).toEqual([]);
  });

  it("returns all transitions for a single status", () => {
    expect(getCommonTransitions(["intake"])).toEqual(
      VALID_TRANSITIONS.intake
    );
  });

  it("returns intersection of transitions for multiple statuses", () => {
    // intake: quarantine, available, under_treatment
    // quarantine: available, under_treatment, deceased
    // common: available, under_treatment
    const result = getCommonTransitions(["intake", "quarantine"]);
    expect(result).toContain("available");
    expect(result).toContain("under_treatment");
    expect(result).not.toContain("quarantine");
    expect(result).not.toContain("deceased");
  });

  it("returns empty when no common transitions", () => {
    // adopted: available
    // deceased: (nothing)
    expect(getCommonTransitions(["adopted", "deceased"])).toEqual([]);
  });
});
