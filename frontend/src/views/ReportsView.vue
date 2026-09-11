<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  fetchReport,
  type CustomerOrderSummary,
  type IngredientInventoryRow,
  type LoyaltyAuditSummary,
  type ProductSalesRow,
  type PromotionUsage,
  type ReportPeriod,
  type ReportResponse,
  type VendorReportRow,
  type EmployeeReportRow,
} from "./reportsApi";
import AppChrome from "@/components/AppChrome.vue";
import FormMessage from "@/components/FormMessage.vue";

type ReportArea =
  "sales" | "promotions" | "inventory" | "products" | "customers" | "vendors" | "employees";

type ProductView = "top_sellers" | "baked_goods" | "drinks";
type CustomerView = "top_customers" | "expiration_audits";

const PAGE_SIZE = 10;

const period = ref<ReportPeriod>("monthly");
const startDate = ref("");
const endDate = ref("");
const report = ref<ReportResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");

const reportArea = ref<ReportArea>("sales");
const productView = ref<ProductView>("top_sellers");
const customerView = ref<CustomerView>("top_customers");
const page = ref(1);

const isCustom = computed(() => period.value === "custom");

const areaOptions: { value: ReportArea; label: string }[] = [
  { value: "sales", label: "Sales" },
  { value: "promotions", label: "Promotions" },
  { value: "inventory", label: "Inventory / ingredients" },
  { value: "products", label: "Products" },
  { value: "customers", label: "Customers / loyalty" },
  { value: "vendors", label: "Vendors" },
  { value: "employees", label: "Employees / operations" },
];

function paginate<T>(rows: T[]): T[] {
  const start = (page.value - 1) * PAGE_SIZE;
  return rows.slice(start, start + PAGE_SIZE);
}

const maxTrendRevenue = computed(() => {
  if (!report.value?.sales.trend.length) {
    return 1;
  }
  return Math.max(...report.value.sales.trend.map((point) => Number(point.revenue)), 1);
});

const displayTrend = computed(() => {
  const trend = report.value?.sales.trend ?? [];
  if (trend.length <= 31) {
    return trend;
  }
  return trend.filter((_, index) => index % 7 === 0 || index === trend.length - 1);
});

const promotionRows = computed(() => report.value?.promotions.promotions ?? []);
const inventoryRows = computed(() => report.value?.inventory.ingredients ?? []);
const productRows = computed((): ProductSalesRow[] => {
  if (!report.value) {
    return [];
  }
  return report.value.products[productView.value];
});
const topCustomerRows = computed(() => report.value?.customers.top_customers ?? []);
const auditRows = computed(() => report.value?.customers.expiration_audits ?? []);
const vendorRows = computed(() => report.value?.vendors.vendors ?? []);
const employeeRows = computed(() => report.value?.employees.employees ?? []);

const activeTotal = computed(() => {
  switch (reportArea.value) {
    case "promotions":
      return promotionRows.value.length;
    case "inventory":
      return inventoryRows.value.length;
    case "products":
      return productRows.value.length;
    case "customers":
      return customerView.value === "top_customers"
        ? topCustomerRows.value.length
        : auditRows.value.length;
    case "vendors":
      return vendorRows.value.length;
    case "employees":
      return employeeRows.value.length;
    default:
      return 0;
  }
});

const totalPages = computed(() => Math.max(1, Math.ceil(activeTotal.value / PAGE_SIZE)));

const pagedPromotions = computed((): PromotionUsage[] => paginate(promotionRows.value));
const pagedInventory = computed((): IngredientInventoryRow[] => paginate(inventoryRows.value));
const pagedProducts = computed((): ProductSalesRow[] => paginate(productRows.value));
const pagedTopCustomers = computed((): CustomerOrderSummary[] => paginate(topCustomerRows.value));
const pagedAudits = computed((): LoyaltyAuditSummary[] => paginate(auditRows.value));
const pagedVendors = computed((): VendorReportRow[] => paginate(vendorRows.value));
const pagedEmployees = computed((): EmployeeReportRow[] => paginate(employeeRows.value));

const showPagination = computed(
  () => reportArea.value !== "sales" && activeTotal.value > PAGE_SIZE,
);

const pageLabel = computed(() => {
  if (activeTotal.value === 0) {
    return "No rows";
  }
  const start = (page.value - 1) * PAGE_SIZE + 1;
  const end = Math.min(page.value * PAGE_SIZE, activeTotal.value);
  return `${start}–${end} of ${activeTotal.value}`;
});

const productHeading = computed(() => {
  if (productView.value === "baked_goods") {
    return "Baked goods sold";
  }
  if (productView.value === "drinks") {
    return "Drinks sold";
  }
  return "Top products";
});

watch([reportArea, productView, customerView, report], () => {
  page.value = 1;
});

watch(totalPages, (pages) => {
  if (page.value > pages) {
    page.value = pages;
  }
});

function formatMoney(value: string | number): string {
  return Number(value).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
  });
}

function formatNumber(value: number): string {
  return value.toLocaleString();
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

async function loadReport(): Promise<void> {
  if (isCustom.value && (!startDate.value || !endDate.value)) {
    errorMessage.value = "Choose both a start and end date for a custom range.";
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  try {
    report.value = await fetchReport({
      period: period.value,
      start_date: isCustom.value || startDate.value ? startDate.value || undefined : undefined,
      end_date: isCustom.value || endDate.value ? endDate.value || undefined : undefined,
    });
    startDate.value = report.value.start_date;
    endDate.value = report.value.end_date;
    page.value = 1;
  } catch (error) {
    report.value = null;
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  } finally {
    loading.value = false;
  }
}

function onPeriodChange(event: Event): void {
  // Read from the event so we don't race v-model's own @change handler.
  const next = (event.target as HTMLSelectElement).value as ReportPeriod;
  period.value = next;
  if (next !== "custom") {
    startDate.value = "";
    endDate.value = "";
    void loadReport();
  }
}

function prevPage(): void {
  page.value = Math.max(1, page.value - 1);
}

function nextPage(): void {
  page.value = Math.min(totalPages.value, page.value + 1);
}

onMounted(() => {
  void loadReport();
});
</script>

<template>
  <main class="page page-top">
    <section class="card card-xl">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Operations reports</p>
      </header>

      <AppChrome />

      <div class="section-header">
        <h2>Business performance</h2>
      </div>
      <p class="hint">Choose a date range and report area. Reporting is read-only.</p>

      <form class="report-filters" @submit.prevent="loadReport">
        <div class="form-field">
          <label for="period">Period</label>
          <select id="period" :value="period" @change="onPeriodChange">
            <option value="monthly">Monthly</option>
            <option value="weekly">Weekly</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div class="form-field">
          <label for="start-date">Start date</label>
          <input id="start-date" v-model="startDate" type="date" :disabled="!isCustom" />
        </div>
        <div class="form-field">
          <label for="end-date">End date</label>
          <input id="end-date" v-model="endDate" type="date" :disabled="!isCustom" />
        </div>
        <div class="form-field report-filters-action">
          <label class="sr-only" for="run-report">Run report</label>
          <button
            id="run-report"
            class="btn btn-primary btn-inline"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? "Loading…" : "Run report" }}
          </button>
        </div>
      </form>

      <FormMessage :text="errorMessage" type="error" />

      <template v-if="report">
        <p class="report-range hint">
          Showing {{ report.start_date }} through {{ report.end_date }} ({{ report.period }}).
        </p>

        <div class="kpi-grid">
          <div class="kpi-card">
            <span class="kpi-label">Revenue</span>
            <strong class="kpi-value">{{ formatMoney(report.sales.total_revenue) }}</strong>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Transactions</span>
            <strong class="kpi-value">{{ formatNumber(report.sales.transaction_count) }}</strong>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Avg order</span>
            <strong class="kpi-value">{{ formatMoney(report.sales.average_order_value) }}</strong>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Points expired</span>
            <strong class="kpi-value">{{
              formatNumber(report.customers.loyalty_points_expired)
            }}</strong>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Active customers</span>
            <strong class="kpi-value">{{ formatNumber(report.customers.active_customers) }}</strong>
          </div>
        </div>

        <div class="report-nav">
          <div class="form-field">
            <label for="report-area">Report area</label>
            <select id="report-area" v-model="reportArea">
              <option v-for="option in areaOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div v-if="reportArea === 'products'" class="form-field">
            <label for="product-view">Product view</label>
            <select id="product-view" v-model="productView">
              <option value="top_sellers">Top sellers</option>
              <option value="baked_goods">Baked goods</option>
              <option value="drinks">Drinks</option>
            </select>
          </div>
          <div v-if="reportArea === 'customers'" class="form-field">
            <label for="customer-view">Customer view</label>
            <select id="customer-view" v-model="customerView">
              <option value="top_customers">Top customers</option>
              <option value="expiration_audits">Loyalty expiration audit</option>
            </select>
          </div>
        </div>

        <section v-if="reportArea === 'sales'" class="report-section">
          <h3>Sales trend</h3>
          <div v-if="displayTrend.length" class="trend-chart" role="img" aria-label="Revenue trend">
            <div
              v-for="point in displayTrend"
              :key="point.date"
              class="trend-bar-wrap"
              :title="`${point.date}: ${formatMoney(point.revenue)}`"
            >
              <div
                class="trend-bar"
                :style="{
                  height: `${Math.max((Number(point.revenue) / maxTrendRevenue) * 100, 2)}%`,
                }"
              />
              <span class="trend-label">{{ point.date.slice(5) }}</span>
            </div>
          </div>
          <p v-else class="empty-note">No sales in this period.</p>

          <div v-if="report.sales.by_item_type.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Item type</th>
                  <th>Qty sold</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in report.sales.by_item_type" :key="row.item_type">
                  <td>{{ formatLabel(row.item_type) }}</td>
                  <td>{{ formatNumber(row.quantity_sold) }}</td>
                  <td>{{ formatMoney(row.revenue) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-else-if="reportArea === 'promotions'" class="report-section">
          <h3>Promotions</h3>
          <p class="hint">
            Estimated usage assumes roughly 15% of qualifying transactions redeem an active promo.
            Total estimated discount: {{ formatMoney(report.promotions.total_estimated_discount) }}.
          </p>
          <div v-if="pagedPromotions.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Discount</th>
                  <th>Window</th>
                  <th>Est. uses</th>
                  <th>Est. discount $</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="promo in pagedPromotions" :key="promo.promo_code">
                  <td>{{ promo.promo_code }}</td>
                  <td>{{ promo.discount_percentage }}%</td>
                  <td>{{ promo.start_date }} – {{ promo.end_date }}</td>
                  <td>{{ formatNumber(promo.estimated_uses) }}</td>
                  <td>{{ formatMoney(promo.estimated_discount_amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty-note">No promotions to report.</p>
        </section>

        <section v-else-if="reportArea === 'inventory'" class="report-section">
          <h3>Inventory / ingredients</h3>
          <p class="hint">
            Stock is simulated from a base of 1,000 units minus recipe usage from drinks sold in the
            period.
          </p>
          <div v-if="pagedInventory.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Ingredient</th>
                  <th>Base stock</th>
                  <th>Consumed</th>
                  <th>Remaining</th>
                  <th>Unit</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in pagedInventory" :key="row.ingredient_id">
                  <td>{{ row.name }}</td>
                  <td>{{ row.base_stock }}</td>
                  <td>{{ row.consumed }}</td>
                  <td>{{ row.remaining }}</td>
                  <td>{{ row.unit_of_measure }}</td>
                  <td>
                    <span
                      class="status-pill"
                      :class="{
                        'status-good': row.status === 'Good',
                        'status-low': row.status === 'Low',
                        'status-out': row.status === 'Out of Stock',
                      }"
                    >
                      {{ row.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty-note">No ingredient inventory to report.</p>
        </section>

        <section v-else-if="reportArea === 'products'" class="report-section">
          <h3>{{ productHeading }}</h3>
          <div v-if="pagedProducts.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th v-if="productView === 'top_sellers'">Type</th>
                  <th>Qty</th>
                  <th>Revenue</th>
                  <th>Cost</th>
                  <th>Profit</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in pagedProducts"
                  :key="`${row.item_type}-${row.item_id}-${row.name}`"
                >
                  <td>{{ row.name }}</td>
                  <td v-if="productView === 'top_sellers'">{{ formatLabel(row.item_type) }}</td>
                  <td>{{ formatNumber(row.quantity_sold) }}</td>
                  <td>{{ formatMoney(row.revenue) }}</td>
                  <td>{{ formatMoney(row.cost) }}</td>
                  <td>{{ formatMoney(row.profit) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty-note">No product sales in this period.</p>
        </section>

        <section v-else-if="reportArea === 'customers'" class="report-section">
          <h3>Customers / loyalty</h3>
          <div class="kpi-grid kpi-grid-compact">
            <div class="kpi-card">
              <span class="kpi-label">Points earned</span>
              <strong class="kpi-value">{{
                formatNumber(report.customers.loyalty_points_earned)
              }}</strong>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Points used (est.)</span>
              <strong class="kpi-value">{{
                formatNumber(report.customers.loyalty_points_used)
              }}</strong>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Buyers in period</span>
              <strong class="kpi-value">{{
                formatNumber(report.customers.customers_with_purchases)
              }}</strong>
            </div>
          </div>

          <template v-if="customerView === 'top_customers'">
            <h4 class="report-subtitle">Top customers</h4>
            <div v-if="pagedTopCustomers.length" class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Orders</th>
                    <th>Items</th>
                    <th>Points earned</th>
                    <th>Favorites</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="customer in pagedTopCustomers" :key="customer.customer_id">
                    <td>{{ customer.first_name }} {{ customer.last_name }}</td>
                    <td>{{ formatNumber(customer.order_count) }}</td>
                    <td>{{ formatNumber(customer.items_purchased) }}</td>
                    <td>{{ formatNumber(customer.loyalty_points_earned) }}</td>
                    <td>
                      {{ customer.favorites.map((favorite) => favorite.name).join(", ") || "—" }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="empty-note">No customer purchases in this period.</p>
          </template>

          <template v-else>
            <h4 class="report-subtitle">Loyalty expiration audit</h4>
            <div v-if="pagedAudits.length" class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Customer ID</th>
                    <th>Points expired</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(audit, index) in pagedAudits"
                    :key="`${audit.expired_at}-${audit.customer_id}-${index}`"
                  >
                    <td>{{ audit.expired_at }}</td>
                    <td>{{ audit.customer_id ?? "—" }}</td>
                    <td>{{ formatNumber(audit.points_expired) }}</td>
                    <td>{{ formatLabel(audit.reason) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="empty-note">No loyalty expirations in this period.</p>
          </template>
        </section>

        <section v-else-if="reportArea === 'vendors'" class="report-section">
          <h3>Vendors</h3>
          <p class="hint">{{ report.vendors.active_count }} active vendors.</p>
          <div v-if="pagedVendors.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Active</th>
                  <th>Contacts</th>
                  <th>Ingredients</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="vendor in pagedVendors" :key="vendor.vendor_id">
                  <td>{{ vendor.name }}</td>
                  <td>{{ vendor.active ? "Yes" : "No" }}</td>
                  <td>{{ vendor.contact_count }}</td>
                  <td>{{ vendor.ingredient_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty-note">No vendors to report.</p>
        </section>

        <section v-else class="report-section">
          <h3>Employees / operations</h3>
          <p class="hint">
            {{ report.employees.active_count }} active staff
            <template v-if="Object.keys(report.employees.by_role).length">
              —
              <span
                v-for="(count, role) in report.employees.by_role"
                :key="role"
                class="role-count"
              >
                {{ count }} {{ role }}{{ count === 1 ? "" : "s" }}
              </span>
            </template>
          </p>
          <div v-if="pagedEmployees.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Hourly rate</th>
                  <th>Hire date</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="employee in pagedEmployees" :key="employee.employee_id">
                  <td>{{ employee.first_name }} {{ employee.last_name }}</td>
                  <td>{{ employee.role }}</td>
                  <td>{{ formatMoney(employee.hourly_rate) }}</td>
                  <td>{{ employee.hire_date }}</td>
                  <td>{{ employee.active ? "Yes" : "No" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty-note">No employees to report.</p>
        </section>

        <nav v-if="showPagination" class="report-pagination" aria-label="Report table pages">
          <button class="btn btn-inline" type="button" :disabled="page <= 1" @click="prevPage">
            Previous
          </button>
          <span class="report-pagination-label">{{ pageLabel }}</span>
          <button
            class="btn btn-inline"
            type="button"
            :disabled="page >= totalPages"
            @click="nextPage"
          >
            Next
          </button>
        </nav>
      </template>
    </section>
  </main>
</template>

<style scoped>
.page-top {
  align-items: flex-start;
}

.card-xl {
  max-width: 1100px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.report-filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  gap: 0.75rem 1rem;
  margin: 1.25rem 0 1rem;
  align-items: end;
}

.report-filters .form-field {
  margin-bottom: 0;
  min-width: 0;
}

.report-filters .form-field:not(.report-filters-action) input,
.report-filters .form-field:not(.report-filters-action) select {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  height: 2.625rem;
  min-height: 2.625rem;
  padding: 0.5rem 0.75rem;
  line-height: 1.25;
}

.report-filters-action {
  display: flex;
  align-items: flex-end;
  width: max-content;
}

.report-range {
  margin: 0 0 1rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.kpi-grid-compact {
  margin-bottom: 1rem;
}

.kpi-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.9rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
}

.kpi-value {
  font-size: 1.25rem;
  color: var(--color-primary-dark);
}

.report-section {
  margin-bottom: 1.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}

.report-section h3 {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  color: var(--color-primary);
}

.report-subtitle {
  margin: 1rem 0 0.5rem;
  font-size: 0.95rem;
  color: var(--color-primary);
}

.report-nav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem 1rem;
  margin: 0 0 1rem;
  align-items: end;
}

.report-nav .form-field {
  margin-bottom: 0;
}

.report-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
}

.report-pagination-label {
  font-size: 0.9rem;
  color: var(--color-muted);
}

.report-pagination .btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.empty-note {
  margin: 0.5rem 0 0;
  color: var(--color-muted);
  font-size: 0.9rem;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 0.35rem;
  height: 140px;
  margin: 0.75rem 0 1rem;
  padding: 0.5rem 0.25rem 0;
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
}

.trend-bar-wrap {
  flex: 1 0 18px;
  min-width: 14px;
  max-width: 36px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 0.25rem;
}

.trend-bar {
  width: 70%;
  min-height: 2px;
  background: var(--color-accent);
  border-radius: 3px 3px 0 0;
}

.trend-label {
  font-size: 0.65rem;
  color: var(--color-muted);
  writing-mode: horizontal-tb;
}

.status-pill {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.status-good {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-low {
  background: #fdf2e9;
  color: #9a4b12;
}

.status-out {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.role-count + .role-count::before {
  content: ", ";
}
</style>
