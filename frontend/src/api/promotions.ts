import { apiFetch } from "./client";
import type { PromotionRead } from "@/types/promotion";

export function apiListPromotions(): Promise<PromotionRead[]> {
  return apiFetch<PromotionRead[]>("/promotions", {}, { contentType: null });
}
