import { computed, ref } from "vue";
import { clearToken, getToken, setToken } from "@/api/client";
import type { EmployeeRole, Session } from "@/types/employee";

function parseJwtPayload(token: string): { sub?: string; role?: string } | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) {
      return null;
    }
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

function readSession(): Session | null {
  const token = getToken();
  if (!token) {
    return null;
  }
  const payload = parseJwtPayload(token);
  if (!payload?.sub || !payload?.role) {
    return null;
  }
  return {
    token,
    employeeId: String(payload.sub),
    role: payload.role as EmployeeRole,
  };
}

const session = ref<Session | null>(readSession());

/** What each role may do in this UI (frontend-only rules). */
const PERMISSIONS = {
  viewOwnProfile: ["employee", "manager", "admin"],
  listEmployees: ["manager", "admin"],
  viewAnyEmployee: ["manager", "admin"],
  viewHourlyRate: ["admin"],
  createEmployee: ["admin"],
  updateEmployee: ["admin"],
  deleteEmployee: ["admin"],
} as const satisfies Record<string, EmployeeRole[]>;

export type PermissionAction = keyof typeof PERMISSIONS;

export function useSession() {
  function login(token: string): void {
    setToken(token);
    session.value = readSession();
  }

  function logout(): void {
    clearToken();
    session.value = null;
  }

  function can(action: PermissionAction): boolean {
    if (!session.value) {
      return false;
    }
    return (PERMISSIONS[action] as readonly string[]).includes(session.value.role);
  }

  return {
    session: computed(() => session.value),
    login,
    logout,
    can,
  };
}
