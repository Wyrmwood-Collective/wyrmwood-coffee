<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { client, authHeaders, extractErrorDetail } from "@/api/client";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { components } from "@/types/api";

type Promotion = components["schemas"]["PromotionRead"];

const promotions = ref<Promotion[]>([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const { data, error } = await client.GET("/promotions");
  if (error) {
    errorMessage.value = "Could not load promotions.";
  } else {
    promotions.value = data;
  }
  loading.value = false;
});

// represents a promotion being in-place edited
interface PromotionDraft {
  active: boolean;
  promo_code: string;
  discount_percentage: string;
  start_date: string;
  end_date: string;
}

const drafts = ref<Record<number, PromotionDraft>>({});
const savingPromotionIds = ref<Set<number>>(new Set());
const deletingPromotionId = ref<number | null>(null);

// the actual rendered values (saved or draft)
const rows = computed(() =>
  promotions.value.map((promotion) => ({
    promotion,
    draft: drafts.value[promotion.id],
  })),
);

function startEdit(promotion: Promotion) {
  drafts.value[promotion.id] = {
    active: promotion.active,
    promo_code: promotion.promo_code,
    discount_percentage: promotion.discount_percentage,
    start_date: promotion.start_date,
    end_date: promotion.end_date,
  };
}

function cancelEdit(promotionId: number) {
  delete drafts.value[promotionId];
}

async function saveEdit(promotionId: number) {
  const draft = drafts.value[promotionId];
  if (!draft) {
    return;
  }

  savingPromotionIds.value.add(promotionId);
  errorMessage.value = "";

  const { data, error } = await client.PUT("/promotions/{id}", {
    params: { path: { id: promotionId } },
    headers: authHeaders(),
    body: draft,
  });

  savingPromotionIds.value.delete(promotionId);

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not save promotion.");
    return;
  }

  const index = promotions.value.findIndex((promotion) => promotion.id === data.id);
  promotions.value[index] = data;
  cancelEdit(promotionId);
}

async function deletePromotion(promotion: Promotion) {
  errorMessage.value = "";
  deletingPromotionId.value = promotion.id;

  const { error } = await client.DELETE("/promotions/{id}", {
    params: { path: { id: promotion.id } },
    headers: authHeaders(),
  });

  deletingPromotionId.value = null;

  if (error) {
    errorMessage.value = extractErrorDetail(error, "Could not delete promotion.");
    return;
  }

  promotions.value = promotions.value.filter((p) => p.id !== promotion.id);
  cancelEdit(promotion.id);
}

// represents a promotion being created
type NewPromotionDraft = PromotionDraft;

function emptyPromotionDraft(): NewPromotionDraft {
  return {
    active: true,
    promo_code: "",
    discount_percentage: "",
    start_date: "",
    end_date: "",
  };
}

const creatingPromotion = ref(false);
const savingNewPromotion = ref(false);
const newPromotionDraft = ref<NewPromotionDraft>(emptyPromotionDraft());

function startCreate() {
  newPromotionDraft.value = emptyPromotionDraft();
  creatingPromotion.value = true;
}

function cancelCreate() {
  creatingPromotion.value = false;
}

async function createPromotion() {
  savingNewPromotion.value = true;
  errorMessage.value = "";

  const { data, error } = await client.POST("/promotions", {
    headers: authHeaders(),
    body: newPromotionDraft.value,
  });

  savingNewPromotion.value = false;

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not create promotion.");
    return;
  }

  promotions.value.push(data);
  creatingPromotion.value = false;
}
</script>

<style scoped>
/* Ledger layout — see VendorsView.vue for the full rationale. Shared
   ledger styling lives in the main stylesheet; only this page's column
   widths stay here. */
.page {
  display: block;
  color: var(--ink);
}

.ledger-head,
.row-main {
  grid-template-columns: 3em 1fr 90px 170px;
}

.detail-line {
  grid-template-columns: 110px 130px 130px;
}

.detail-field {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
}

.field-label {
  flex: 0 0 auto;
  font-size: 0.78em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--ink-soft);
}

.detail-field .field {
  flex: 1 1 auto;
  min-width: 0;
}
</style>

<template>
  <main class="page">
    <h1>Promotions</h1>
    <FormMessage :text="errorMessage" type="error" />
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-toolbar">
        <LinkButton :disabled="creatingPromotion" @click="startCreate">
          New promotion
        </LinkButton>
      </div>
      <div class="ledger-head">
        <span class="row-id">ID</span>
        <span>Promo Code</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li v-if="creatingPromotion" class="ledger-row">
          <div class="row-main">
            <span class="row-id">new</span>
            <input
              v-model="newPromotionDraft.promo_code"
              type="text"
              class="field"
              placeholder="Promo code"
            />
            <select v-model="newPromotionDraft.active" class="field">
              <option :value="true">true</option>
              <option :value="false">false</option>
            </select>
            <span class="row-actions">
              <LinkButton :disabled="savingNewPromotion" @click="createPromotion">
                {{ savingNewPromotion ? "Saving..." : "Save" }}
              </LinkButton>
              <LinkButton :disabled="savingNewPromotion" @click="cancelCreate">
                Cancel
              </LinkButton>
            </span>
          </div>
          <div class="detail-line">
            <span class="detail-field">
              <span class="field-label">Discount</span>
              <input
                v-model="newPromotionDraft.discount_percentage"
                type="text"
                class="field"
                placeholder="Discount %"
              />
            </span>
            <span class="detail-field">
              <span class="field-label">Start</span>
              <input v-model="newPromotionDraft.start_date" type="date" class="field" />
            </span>
            <span class="detail-field">
              <span class="field-label">End</span>
              <input v-model="newPromotionDraft.end_date" type="date" class="field" />
            </span>
          </div>
        </li>
        <li v-for="row in rows" :key="row.promotion.id" class="ledger-row">
          <div class="row-main">
            <span class="row-id">{{ row.promotion.id }}</span>
            <template v-if="row.draft">
              <input v-model="row.draft.promo_code" type="text" class="field" />
              <select v-model="row.draft.active" class="field">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
              <span class="row-actions">
                <LinkButton
                  :disabled="savingPromotionIds.has(row.promotion.id)"
                  @click="saveEdit(row.promotion.id)"
                >
                  {{ savingPromotionIds.has(row.promotion.id) ? "Saving..." : "Save" }}
                </LinkButton>
                <LinkButton
                  :disabled="savingPromotionIds.has(row.promotion.id)"
                  @click="cancelEdit(row.promotion.id)"
                >
                  Cancel
                </LinkButton>
              </span>
            </template>
            <template v-else>
              <span>{{ row.promotion.promo_code }}</span>
              <span>{{ row.promotion.active }}</span>
              <span class="row-actions">
                <LinkButton @click="startEdit(row.promotion)">Edit</LinkButton>
                <LinkButton
                  :disabled="deletingPromotionId === row.promotion.id"
                  @click="deletePromotion(row.promotion)"
                >
                  {{ deletingPromotionId === row.promotion.id ? "Deleting..." : "Delete" }}
                </LinkButton>
              </span>
            </template>
          </div>
          <div v-if="row.draft" class="detail-line">
            <span class="detail-field">
              <span class="field-label">Discount</span>
              <input
                v-model="row.draft.discount_percentage"
                type="text"
                class="field"
                placeholder="Discount %"
              />
            </span>
            <span class="detail-field">
              <span class="field-label">Start</span>
              <input v-model="row.draft.start_date" type="date" class="field" />
            </span>
            <span class="detail-field">
              <span class="field-label">End</span>
              <input v-model="row.draft.end_date" type="date" class="field" />
            </span>
          </div>
          <div v-else class="detail-line">
            <span class="detail-field">
              <span class="field-label">Discount</span>
              <span>{{ row.promotion.discount_percentage }}%</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Start</span>
              <span>{{ row.promotion.start_date }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">End</span>
              <span>{{ row.promotion.end_date }}</span>
            </span>
          </div>
        </li>
      </ul>
    </template>
  </main>
</template>
