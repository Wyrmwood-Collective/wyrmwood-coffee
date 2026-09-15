export interface PromotionRead {
  id: number;
  active: boolean;
  promo_code: string;
  discount_percentage: string;
  start_date: string;
  end_date: string;
}
