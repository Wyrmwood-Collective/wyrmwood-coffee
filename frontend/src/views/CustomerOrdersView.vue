<script setup lang="ts">
import { computed, ref } from "vue";
import { apiListCustomers, resolveActiveCustomer } from "@/api/customers";
import { filterCustomerOrderHistory, loadAllPurchases } from "@/api/purchases";
import { apiListPromotions } from "@/api/promotions";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { CustomerRead } from "@/types/customer";
import type { PromotionRead } from "@/types/promotion";
import type { PurchaseHistoryRead } from "@/types/purchase";

const PAGE_SIZE = 5;

/** Session cache — search only runs on submit; skip refetch on later lookups. */
let customersCache: CustomerRead[] | null = null;
let promotionsCache: PromotionRead[] | null = null;

const phoneInput = ref("");
const emailInput = ref("");
const searching = ref(false);
const errorMessage = ref("");
const infoMessage = ref("");

const customer = ref<CustomerRead | null>(null);
const orders = ref<PurchaseHistoryRead[]>([]);
const selected = ref<PurchaseHistoryRead | null>(null);
const currentPage = ref(1);

const customerLabel = computed(() => {
  if (!customer.value) {
    return "";
  }
  return `#${customer.value.id} ${customer.value.first_name} ${customer.value.last_name}`;
});

const totalPages = computed(() =>
  orders.value.length === 0 ? 0 : Math.ceil(orders.value.length / PAGE_SIZE),
);

const pageOrders = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return orders.value.slice(start, start + PAGE_SIZE);
});

const pageRangeLabel = computed(() => {
  if (orders.value.length === 0) {
    return "No orders";
  }
  const start = (currentPage.value - 1) * PAGE_SIZE + 1;
  const end = Math.min(currentPage.value * PAGE_SIZE, orders.value.length);
  return `Showing ${start}–${end} of ${orders.value.length}`;
});

const canGoPrev = computed(() => currentPage.value > 1);
const canGoNext = computed(() => currentPage.value < totalPages.value);

function formatPhoneDigits(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 10);
  if (digits.length <= 3) {
    return digits;
  }
  if (digits.length <= 6) {
    return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  }
  return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
}

function onPhoneInput(event: Event) {
  const target = event.target as HTMLInputElement;
  phoneInput.value = formatPhoneDigits(target.value);
}

function formatMoney(value: string): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return value;
  }
  return amount.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function formatItems(order: PurchaseHistoryRead): string {
  return order.items.map((item) => `${item.quantity}× ${item.name}`).join(", ");
}

function contactHint(person: CustomerRead): string {
  const parts: string[] = [];
  if (person.phone) {
    parts.push(`Phone ${person.phone}`);
  }
  if (person.email) {
    parts.push(person.email);
  }
  return parts.join(" · ");
}

function resetResults() {
  customer.value = null;
  orders.value = [];
  selected.value = null;
  currentPage.value = 1;
}

function goNewer() {
  if (!canGoPrev.value) {
    return;
  }
  currentPage.value -= 1;
  selected.value = null;
}

function goOlder() {
  if (!canGoNext.value) {
    return;
  }
  currentPage.value += 1;
  selected.value = null;
}

async function loadCustomersAndPromotions(): Promise<{
  customers: CustomerRead[];
  promotions: PromotionRead[];
}> {
  const [customers, promotions] = await Promise.all([
    customersCache
      ? Promise.resolve(customersCache)
      : apiListCustomers().then((data) => {
          customersCache = data;
          return data;
        }),
    promotionsCache
      ? Promise.resolve(promotionsCache)
      : apiListPromotions().then((data) => {
          promotionsCache = data;
          return data;
        }),
  ]);
  return { customers, promotions };
}

async function searchCustomer() {
  errorMessage.value = "";
  infoMessage.value = "";
  resetResults();

  const phone = phoneInput.value.trim();
  const email = emailInput.value.trim();

  searching.value = true;
  try {
    const { customers, promotions } = await loadCustomersAndPromotions();

    const result = resolveActiveCustomer(customers, { phone, email });
    if (!result.ok) {
      errorMessage.value = result.error;
      return;
    }

    customer.value = result.customer;

    const purchases = loadAllPurchases();
    orders.value = filterCustomerOrderHistory(purchases, result.customer.id, promotions);
    currentPage.value = 1;

    if (result.notice && orders.value.length === 0) {
      infoMessage.value = `${result.notice} This customer has no recorded orders.`;
    } else if (result.notice) {
      infoMessage.value = result.notice;
    } else if (orders.value.length === 0) {
      infoMessage.value = "This customer has no recorded orders.";
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  } finally {
    searching.value = false;
  }
}

function viewOrder(order: PurchaseHistoryRead) {
  selected.value = order;
}
</script>

<template>
  <main class="orders-page">
    <h1>Order History</h1>

    <p class="orders-hint">
      Look up an active customer by phone or email to review their purchases and loyalty activity.
      Guest orders are not included.
    </p>

    <form class="orders-search" @submit.prevent="searchCustomer">
      <div class="orders-field">
        <label for="customer-phone">Phone number</label>
        <input
          id="customer-phone"
          :value="phoneInput"
          type="tel"
          inputmode="numeric"
          autocomplete="tel-national"
          placeholder="206-555-0101"
          maxlength="12"
          @input="onPhoneInput"
        />
      </div>
      <div class="orders-field">
        <label for="customer-email">Email</label>
        <input
          id="customer-email"
          v-model="emailInput"
          type="email"
          autocomplete="email"
          placeholder="ava.thompson@example.com"
        />
      </div>
      <div class="orders-submit">
        <LinkButton type="submit" :disabled="searching">
          {{ searching ? "Searching…" : "Find customer" }}
        </LinkButton>
      </div>
    </form>

    <FormMessage :text="errorMessage" type="error" />
    <FormMessage :text="infoMessage" type="success" />

    <section v-if="customer" class="orders-customer">
      <h2>{{ customerLabel }}</h2>
      <p class="orders-hint">
        {{ contactHint(customer) }} · {{ customer.loyalty_points }} loyalty points
        <template v-if="customer.loyalty_expires_at">
          (expires {{ formatDateTime(customer.loyalty_expires_at) }})
        </template>
      </p>
    </section>

    <div v-if="orders.length" class="orders-ledger">
      <div class="orders-table-wrap">
        <table class="orders-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Date &amp; time</th>
              <th>Items</th>
              <th>Promo</th>
              <th>Tax</th>
              <th>Total</th>
              <th>Points</th>
              <th></th>
            </tr>
          </thead>
          <tbody :key="currentPage">
            <tr v-for="order in pageOrders" :key="order.id">
              <td>{{ order.id }}</td>
              <td>{{ formatDateTime(order.created_at) }}</td>
              <td>{{ formatItems(order) }}</td>
              <td>{{ order.promo_code || "—" }}</td>
              <td>{{ formatMoney(order.tax) }}</td>
              <td>{{ formatMoney(order.total) }}</td>
              <td>{{ order.loyalty_points_earned }}</td>
              <td>
                <LinkButton @click="viewOrder(order)">View</LinkButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <nav class="orders-pager" aria-label="Order history pages">
        <button type="button" class="orders-turn" :disabled="!canGoPrev" @click="goNewer">
          ← Newer
        </button>
        <div class="orders-pager-meta">
          <p class="orders-leaf">Leaf {{ currentPage }} of {{ totalPages }}</p>
          <p class="orders-range">{{ pageRangeLabel }}</p>
        </div>
        <button type="button" class="orders-turn" :disabled="!canGoNext" @click="goOlder">
          Older →
        </button>
      </nav>
    </div>

    <section v-if="selected" class="orders-detail">
      <h3>Order #{{ selected.id }}</h3>
      <dl class="orders-detail-list">
        <div>
          <dt>Date &amp; time</dt>
          <dd>{{ formatDateTime(selected.created_at) }}</dd>
        </div>
        <div>
          <dt>Promotion code</dt>
          <dd>{{ selected.promo_code || "None" }}</dd>
        </div>
        <div>
          <dt>Subtotal</dt>
          <dd>{{ formatMoney(selected.subtotal) }}</dd>
        </div>
        <div>
          <dt>Tax</dt>
          <dd>{{ formatMoney(selected.tax) }}</dd>
        </div>
        <div>
          <dt>Final total</dt>
          <dd>{{ formatMoney(selected.total) }}</dd>
        </div>
        <div>
          <dt>Loyalty points earned</dt>
          <dd>{{ selected.loyalty_points_earned }}</dd>
        </div>
      </dl>

      <h4 class="orders-subhead">Items purchased</h4>
      <div class="orders-table-wrap">
        <table class="orders-table">
          <thead>
            <tr>
              <th>Item</th>
              <th v-if="selected.items.some((item) => item.item_type)">Type</th>
              <th>Qty</th>
              <th>Unit price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in selected.items" :key="item.id">
              <td>{{ item.name }}</td>
              <td v-if="selected.items.some((row) => row.item_type)">
                {{ item.item_type || "—" }}
              </td>
              <td>{{ item.quantity }}</td>
              <td>{{ formatMoney(item.unit_price) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<style scoped>
/* Local tokens — fallbacks keep the view intact if shared CSS vars change. */
.orders-page {
  --orders-ink: var(--ink, #2b2420);
  --orders-ink-soft: var(--ink-soft, #6b5f4f);
  --orders-page: var(--page, #f4ecd8);
  --orders-accent: rgba(120, 86, 32, 0.1);
  --orders-line: rgba(43, 36, 32, 0.18);
  --orders-line-strong: rgba(43, 36, 32, 0.35);
  --orders-panel: rgba(255, 248, 228, 0.45);
  --orders-font-display: "MedievalSharp", Georgia, serif;

  display: block;
  width: 100%;
  color: var(--orders-ink);
}

.orders-hint {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: var(--orders-ink-soft);
}

.orders-search {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  margin: 1rem 0 1.25rem;
}

.orders-field {
  flex: 1 1 200px;
  margin: 0;
}

.orders-field label {
  display: block;
  margin-bottom: 0.35rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--orders-ink);
}

.orders-field input {
  box-sizing: border-box;
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--orders-line-strong);
  border-radius: 2px;
  font: inherit;
  color: var(--orders-ink);
  background: rgba(255, 255, 255, 0.55);
}

.orders-field input:focus {
  outline: 2px solid rgba(120, 86, 32, 0.45);
  outline-offset: 1px;
  border-color: rgba(120, 86, 32, 0.55);
}

.orders-submit {
  display: flex;
  align-items: center;
  /* Offsets the button's text baseline to match the phone/email inputs':
     their text sits above their box's bottom edge by their vertical
     padding (0.65rem) plus their 1px border, so this reproduces that same
     inset on the button's otherwise unpadded box. */
  padding-bottom: calc(0.65rem + 1px);
}

.orders-customer {
  margin: 0 0 1rem;
}

.orders-customer h2 {
  margin: 0 0 0.25rem;
  font-family: var(--orders-font-display);
  font-size: 1.1rem;
  font-weight: 400;
  color: var(--orders-ink);
}

.orders-table-wrap {
  overflow-x: auto;
  margin-bottom: 0.25rem;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.orders-table th,
.orders-table td {
  padding: 0.65rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--orders-line);
  vertical-align: top;
}

.orders-table th {
  font-family: var(--orders-font-display);
  font-weight: 400;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: var(--orders-ink-soft);
  border-bottom: 3px double var(--orders-line-strong);
}

.orders-table tbody tr:hover {
  background: var(--orders-accent);
}

.orders-pager {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.75rem 1rem;
  margin-top: 0.85rem;
  padding: 0.85rem 0 0.15rem;
  border-top: 3px double var(--orders-line-strong);
}

.orders-pager-meta {
  text-align: center;
  min-width: 0;
}

.orders-leaf {
  margin: 0;
  font-family: var(--orders-font-display);
  font-size: 1rem;
  letter-spacing: 0.05em;
  color: var(--orders-ink);
}

.orders-range {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--orders-ink-soft);
}

.orders-turn {
  appearance: none;
  border: 1px solid rgba(43, 36, 32, 0.28);
  background: var(--orders-panel);
  color: var(--orders-ink);
  font: inherit;
  font-family: var(--orders-font-display);
  font-size: 0.9rem;
  letter-spacing: 0.03em;
  padding: 0.4rem 0.75rem;
  border-radius: 2px;
  cursor: pointer;
}

.orders-turn:hover:not(:disabled) {
  background: var(--orders-accent);
  border-color: rgba(43, 36, 32, 0.45);
}

.orders-turn:disabled {
  opacity: 0.4;
  cursor: default;
}

.orders-detail {
  margin-top: 1rem;
  padding: 1rem;
  background: var(--orders-panel);
  border: 1px solid rgba(43, 36, 32, 0.2);
  border-radius: 2px;
}

.orders-detail h3 {
  margin: 0 0 0.75rem;
  font-family: var(--orders-font-display);
  font-size: 1.05rem;
  font-weight: 400;
  color: var(--orders-ink);
}

.orders-detail-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem 1rem;
  margin: 0 0 0.5rem;
}

.orders-detail-list div {
  margin: 0;
}

.orders-detail-list dt {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--orders-ink-soft);
}

.orders-detail-list dd {
  margin: 0.15rem 0 0;
  font-weight: 600;
  color: var(--orders-ink);
}

.orders-subhead {
  margin: 1rem 0 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--orders-ink-soft);
}

@media (max-width: 560px) {
  .orders-pager {
    grid-template-columns: 1fr 1fr;
  }

  .orders-pager-meta {
    grid-column: 1 / -1;
    order: -1;
  }
}
</style>
