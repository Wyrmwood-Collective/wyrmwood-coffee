import createClient from "openapi-fetch";
import type { paths } from "@/types/api";

export const client = createClient<paths>({
  baseUrl: "/",
});

const TOKEN_KEY = "wyrmwood_access_token";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

/** Bearer-auth header for endpoints that require a signed-in employee. */
export function authHeaders(): Record<string, string> {
  return { Authorization: `Bearer ${getToken()}` };
}

// A FastAPI/Pydantic validation error item, e.g. from a 422 response:
// { loc: ["body", "contacts", 0, "email"], msg: "..." }
function formatValidationError(item: unknown): string | null {
  if (typeof item !== "object" || item === null || !("msg" in item)) {
    return null;
  }
  const { loc, msg } = item as { loc?: unknown; msg?: unknown };
  if (typeof msg !== "string") {
    return null;
  }
  if (Array.isArray(loc)) {
    // "body" just means "in the request body" — not meaningful to a user.
    const field = loc.filter((segment) => segment !== "body").join(".");
    if (field) {
      return `${field}: ${msg}`;
    }
  }
  return msg;
}

/**
 * Pulls the specific error message out of an openapi-fetch error, if present.
 * FastAPI's `detail` is either a plain string (raised via HTTPException) or,
 * for a 422, a list of Pydantic validation errors — handles both.
 */
export function extractErrorDetail(error: unknown, fallback: string): string {
  if (typeof error !== "object" || error === null || !("detail" in error)) {
    return fallback;
  }

  const detail = (error as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map(formatValidationError)
      .filter((message): message is string => message !== null);
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  return fallback;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Legacy fetch helper for endpoints not yet migrated to the typed client. */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  { contentType = "application/json" as string | null } = {},
): Promise<T> {
  const headers: Record<string, string> = { ...authHeaders() };
  if (contentType) {
    headers["Content-Type"] = contentType;
  }

  const response = await fetch(path, {
    ...init,
    headers: { ...headers, ...init.headers },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      extractErrorDetail(data, "Something went wrong. Please try again."),
      response.status,
    );
  }
  return data as T;
}
