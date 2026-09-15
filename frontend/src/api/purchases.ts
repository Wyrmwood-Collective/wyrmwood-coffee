import sampleData from "@sample-data";
import type { PromotionRead } from "@/types/promotion";
import type { PurchaseHistoryRead, PurchaseItemRead, SamplePurchase } from "@/types/purchase";

type SampleDataFile = {
  purchases?: SamplePurchase[];
  purchases_histories?: SamplePurchase[];
};

/**
 * Load WC-69 sample purchases (or a `purchases` key if present).
 * There is no GET /purchases endpoint — the barista UI pulls this data
 * and filters it on the client.
 */
export function loadAllPurchases(): SamplePurchase[] {
  const data = sampleData as SampleDataFile;
  return data.purchases ?? data.purchases_histories ?? [];
}

function money(value: number | string): string {
  return Number(value).toFixed(2);
}

function enrichPurchase(
  raw: SamplePurchase,
  index: number,
  promoById: Map<number, string>,
): PurchaseHistoryRead {
  const id = raw.id ?? index + 1;
  const total = Number(raw.total);
  const items: PurchaseItemRead[] = raw.items.map((item, itemIndex) => ({
    id: itemIndex + 1,
    purchase_id: id,
    item_type: item.item_type ?? "",
    name: item.name,
    quantity: item.quantity,
    unit_price: money(item.unit_price),
  }));

  return {
    id,
    customer_id: raw.customer_id,
    promo_id: raw.promo_id,
    subtotal: money(raw.subtotal),
    tax: money(raw.tax),
    total: money(raw.total),
    created_at: raw.created_at,
    items,
    promo_code: raw.promo_id != null ? (promoById.get(raw.promo_id) ?? null) : null,
    loyalty_points_earned: Math.floor(total),
  };
}

/**
 * Customer order history: exclude guests, keep this customer only,
 * newest → oldest. Enrich with promo codes and loyalty points.
 */
export function filterCustomerOrderHistory(
  purchases: SamplePurchase[],
  customerId: number,
  promotions: PromotionRead[],
): PurchaseHistoryRead[] {
  const promoById = new Map(promotions.map((promo) => [promo.id, promo.promo_code]));

  return purchases
    .map((purchase, index) => enrichPurchase(purchase, index, promoById))
    .filter((purchase) => purchase.customer_id === customerId)
    .sort((a, b) => {
      const byDate = new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (byDate !== 0) {
        return byDate;
      }
      return b.id - a.id;
    });
}
