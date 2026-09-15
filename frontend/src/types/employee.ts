import type { components } from "@/types/api";

export type EmployeeRole = components["schemas"]["EmployeeRole"];
export type EmployeeRead = components["schemas"]["EmployeeRead"];
export type EmployeeCreateInput = components["schemas"]["EmployeeCreate"];

export interface Session {
  token: string;
  employeeId: string;
  role: EmployeeRole;
}
