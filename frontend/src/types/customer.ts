export interface CustomerRead {
  id: number;
  active: boolean;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  loyalty_points: number;
  loyalty_expires_at: string;
}
