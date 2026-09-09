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

function formatApiError(data: unknown): string {
  if (!data || typeof data !== "object") {
    return "Something went wrong. Please try again.";
  }
  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(" ");
  }
  return "Something went wrong. Please try again.";
}

function authHeaders(contentType: string | null = "application/json"): HeadersInit {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  return headers;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  { contentType = "application/json" as string | null } = {},
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { ...authHeaders(contentType), ...init.headers },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(formatApiError(data), response.status);
  }
  return data as T;
}
