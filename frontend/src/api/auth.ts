import type { components } from "@/types/api";
import { client } from "@/api/client";

type Token = components["schemas"]["Token"];

export async function apiLogin(username: string, password: string): Promise<Token> {
  const response = await client.POST("/auth/login", {
    body: {
      username,
      password,
      scope: "",
    },
    bodySerializer(body) {
      const params = new URLSearchParams();
      for (const [key, value] of Object.entries(body)) {
        if (value !== undefined) params.set(key, String(value));
      }
      return params.toString();
    },
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  if (!response.data) {
    const detail =
      typeof response.error === "object" && response.error !== null && "detail" in response.error
        ? String((response.error as { detail?: unknown }).detail)
        : "Login failed";
    throw new Error(detail);
  }

  return response.data;
}

export async function apiLogout(): Promise<void> {
  fetch("localhost:8000/auth/logout", { method: "POST" });
}
