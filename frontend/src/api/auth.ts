import { apiFetch } from "./client";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function apiLogin(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  return apiFetch<TokenResponse>(
    "/auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    },
    { contentType: null },
  );
}

export async function apiLogout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}
