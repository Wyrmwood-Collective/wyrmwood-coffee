export type EmployeeRole = "employee" | "manager" | "admin";

export interface EmployeeRead {
  id: number;
  active: boolean;
  first_name: string;
  last_name: string;
  role: EmployeeRole;
  hourly_rate: string;
  hire_date: string;
  term_date: string | null;
  username: string;
}

export interface EmployeeCreateInput {
  first_name: string;
  last_name: string;
  username: string;
  password: string;
  role: EmployeeRole;
  hourly_rate: string;
  hire_date: string;
  term_date?: string;
  active: boolean;
}

export interface Session {
  token: string;
  employeeId: string;
  role: EmployeeRole;
}
