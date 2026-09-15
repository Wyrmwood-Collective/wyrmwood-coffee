import { apiFetch } from "@/api/client";

/** Local to ReportsView — keep out of shared `api/` during site overhaul. */

export type ReportPeriod = "monthly" | "weekly" | "custom";
export type InventoryStatus = "Good" | "Low" | "Out of Stock";

export interface SalesTrendPoint {
  date: string;
  revenue: string;
  transactions: number;
}

export interface SalesByType {
  item_type: string;
  quantity_sold: number;
  revenue: string;
}

export interface SalesReport {
  total_revenue: string;
  transaction_count: number;
  line_item_count: number;
  average_order_value: string;
  by_item_type: SalesByType[];
  trend: SalesTrendPoint[];
}

export interface PromotionUsage {
  promo_code: string;
  discount_percentage: string;
  start_date: string;
  end_date: string;
  estimated_uses: number;
  estimated_discount_amount: string;
}

export interface PromotionsReport {
  promotions: PromotionUsage[];
  total_estimated_uses: number;
  total_estimated_discount: string;
}

export interface IngredientInventoryRow {
  ingredient_id: number;
  name: string;
  unit_of_measure: string;
  base_stock: string;
  consumed: string;
  remaining: string;
  status: InventoryStatus;
  vendor_id: number;
}

export interface InventoryReport {
  ingredients: IngredientInventoryRow[];
}

export interface ProductSalesRow {
  item_type: string;
  item_id: number;
  name: string;
  quantity_sold: number;
  revenue: string;
  cost: string;
  profit: string;
}

export interface ProductsReport {
  top_sellers: ProductSalesRow[];
  baked_goods: ProductSalesRow[];
  drinks: ProductSalesRow[];
}

export interface CustomerFavorite {
  item_type: string;
  item_id: number;
  name: string;
  quantity: number;
}

export interface CustomerOrderSummary {
  customer_id: number;
  first_name: string;
  last_name: string;
  order_count: number;
  items_purchased: number;
  loyalty_points_earned: number;
  favorites: CustomerFavorite[];
}

export interface LoyaltyAuditSummary {
  points_expired: number;
  reason: string;
  expired_at: string;
  customer_id: number | null;
}

export interface CustomersLoyaltyReport {
  active_customers: number;
  customers_with_purchases: number;
  loyalty_points_earned: number;
  loyalty_points_used: number;
  loyalty_points_expired: number;
  expiration_audits: LoyaltyAuditSummary[];
  top_customers: CustomerOrderSummary[];
}

export interface VendorReportRow {
  vendor_id: number;
  name: string;
  active: boolean;
  contact_count: number;
  ingredient_count: number;
}

export interface VendorsReport {
  vendors: VendorReportRow[];
  active_count: number;
}

export interface EmployeeReportRow {
  employee_id: number;
  first_name: string;
  last_name: string;
  role: string;
  hourly_rate: string;
  hire_date: string;
  active: boolean;
}

export interface EmployeesReport {
  employees: EmployeeReportRow[];
  active_count: number;
  by_role: Record<string, number>;
}

export interface ReportResponse {
  period: ReportPeriod;
  start_date: string;
  end_date: string;
  sales: SalesReport;
  promotions: PromotionsReport;
  inventory: InventoryReport;
  products: ProductsReport;
  customers: CustomersLoyaltyReport;
  vendors: VendorsReport;
  employees: EmployeesReport;
}

export interface ReportQuery {
  period: ReportPeriod;
  start_date?: string;
  end_date?: string;
}

export function fetchReport(query: ReportQuery): Promise<ReportResponse> {
  const params = new URLSearchParams({ period: query.period });
  if (query.start_date) {
    params.set("start_date", query.start_date);
  }
  if (query.end_date) {
    params.set("end_date", query.end_date);
  }
  return apiFetch<ReportResponse>(`/reports?${params.toString()}`, {}, { contentType: null });
}
