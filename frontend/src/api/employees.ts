import { apiFetch, ApiError } from "./client";
import type { EmployeeCreateInput, EmployeeRead } from "@/types/employee";

export function apiListEmployees(): Promise<EmployeeRead[]> {
  return apiFetch<EmployeeRead[]>("/employees", {}, { contentType: null });
}

export function apiGetEmployee(id: string | number): Promise<EmployeeRead> {
  return apiFetch<EmployeeRead>(`/employees/${id}`, {}, { contentType: null });
}

export function apiCreateEmployee(payload: EmployeeCreateInput): Promise<EmployeeRead> {
  return apiFetch<EmployeeRead>("/employees", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiDeleteEmployee(id: string | number): Promise<void> {
  try {
    await apiFetch<void>(`/employees/${id}`, { method: "DELETE" }, { contentType: null });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 405)) {
      throw new Error(
        "Delete is not available yet — the API needs a DELETE /employees/{id} endpoint.",
      );
    }
    throw error;
  }
}
