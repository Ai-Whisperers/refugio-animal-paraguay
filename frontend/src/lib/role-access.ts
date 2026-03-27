/**
 * Role-based access control utilities for admin navigation.
 *
 * Determines which menu items a user can see based on their JWT role.
 * Roles are hierarchical: admin > staff > adopter.
 */

import type { UserRole } from "@/types/api";

/** Roles ordered by privilege level (highest first). */
const ROLE_HIERARCHY: UserRole[] = ["admin", "staff", "adopter"];

/**
 * Check if the user's role meets or exceeds the required role.
 * Admin can see everything; staff can see staff-level items; adopter is lowest.
 * If no requiredRole is set, the item is visible to all authenticated users.
 */
export function hasRoleAccess(userRole: UserRole | null, requiredRole?: UserRole): boolean {
  if (!requiredRole) return true;
  if (!userRole) return false;
  const userLevel = ROLE_HIERARCHY.indexOf(userRole);
  const requiredLevel = ROLE_HIERARCHY.indexOf(requiredRole);
  // Lower index = higher privilege
  return userLevel >= 0 && userLevel <= requiredLevel;
}
