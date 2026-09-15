export interface PurchaseItemRead {
  id: number;
  purchase_id: number;
  item_type: string;
  name: string;
  quantity: number;
  unit_price: string;
}

export interface PurchaseHistoryRead {
  id: number;
  customer_id: number | null;
  promo_id: number | null;
  subtotal: string;
  tax: string;
  total: string;
  created_at: string;
  items: PurchaseItemRead[];
  promo_code: string | null;
  loyalty_points_earned: number;
}

/** Shape of WC-69 sample purchase rows before frontend normalization. */
export interface SamplePurchase {
  id?: number;
  customer_id: number | null;
  promo_id: number | null;
  subtotal: number | string;
  tax: number | string;
  total: number | string;
  created_at: string;
  items: Array<{
    name: string;
    quantity: number;
    unit_price: number | string;
    item_type?: string;
  }>;
}
