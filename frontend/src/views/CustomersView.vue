<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { client, authHeaders, extractErrorDetail } from "@/api/client";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { components } from "@/types/api";

type Customer = components["schemas"]["CustomerRead"];

function formatDate(isoDateTime: string): string {
  return isoDateTime.slice(0, 10);
}

const customers = ref<Customer[]>([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const { data, error } = await client.GET("/customers");
  if (error) {
    errorMessage.value = "Could not load customers.";
  } else {
    customers.value = data;
  }
  loading.value = false;
});

// represents a customer being in-place edited. loyalty_expires_at is never
// edited here, so it always comes through from the original record.
interface CustomerDraft {
  active: boolean;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  loyalty_points: number;
}

const drafts = ref<Record<number, CustomerDraft>>({});
const savingCustomerIds = ref<Set<number>>(new Set());
const deletingCustomerId = ref<number | null>(null);

// the actual rendered values (saved or draft)
const rows = computed(() =>
  customers.value.map((customer) => ({
    customer,
    draft: drafts.value[customer.id],
  })),
);

function startEdit(customer: Customer) {
  drafts.value[customer.id] = {
    active: customer.active,
    first_name: customer.first_name,
    last_name: customer.last_name,
    email: customer.email ?? null,
    phone: customer.phone ?? null,
    loyalty_points: customer.loyalty_points,
  };
}

function cancelEdit(customerId: number) {
  delete drafts.value[customerId];
}

async function saveEdit(customerId: number) {
  const draft = drafts.value[customerId];
  if (!draft) {
    return;
  }

  savingCustomerIds.value.add(customerId);
  errorMessage.value = "";

  const { data, error } = await client.PUT("/customers/{id}", {
    params: { path: { id: customerId } },
    headers: authHeaders(),
    body: draft,
  });

  savingCustomerIds.value.delete(customerId);

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not save customer.");
    return;
  }

  const index = customers.value.findIndex((customer) => customer.id === data.id);
  customers.value[index] = data;
  cancelEdit(customerId);
}

async function deleteCustomer(customer: Customer) {
  errorMessage.value = "";
  deletingCustomerId.value = customer.id;

  const { error } = await client.DELETE("/customers/{id}", {
    params: { path: { id: customer.id } },
    headers: authHeaders(),
  });

  deletingCustomerId.value = null;

  if (error) {
    errorMessage.value = extractErrorDetail(error, "Could not delete customer.");
    return;
  }

  customers.value = customers.value.filter((c) => c.id !== customer.id);
  cancelEdit(customer.id);
}

// represents a customer being created
interface NewCustomerDraft {
  active: boolean;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  loyalty_points: number;
}

function emptyCustomerDraft(): NewCustomerDraft {
  return {
    active: true,
    first_name: "",
    last_name: "",
    email: null,
    phone: null,
    loyalty_points: 0,
  };
}

const creatingCustomer = ref(false);
const savingNewCustomer = ref(false);
const newCustomerDraft = ref<NewCustomerDraft>(emptyCustomerDraft());

function startCreate() {
  newCustomerDraft.value = emptyCustomerDraft();
  creatingCustomer.value = true;
}

function cancelCreate() {
  creatingCustomer.value = false;
}

async function createCustomer() {
  savingNewCustomer.value = true;
  errorMessage.value = "";

  const { data, error } = await client.POST("/customers", {
    headers: authHeaders(),
    body: newCustomerDraft.value,
  });

  savingNewCustomer.value = false;

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not create customer.");
    return;
  }

  customers.value.push(data);
  creatingCustomer.value = false;
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
  grid-template-columns: 3em 1fr 1fr 90px 170px;
}

.detail-line {
  grid-template-columns: 230px 130px 90px 150px;
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
    <h1>Customers</h1>
    <FormMessage :text="errorMessage" type="error" />
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-toolbar">
        <LinkButton :disabled="creatingCustomer" @click="startCreate">
          New customer
        </LinkButton>
      </div>
      <div class="ledger-head">
        <span class="row-id">ID</span>
        <span>First Name</span>
        <span>Last Name</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li v-if="creatingCustomer" class="ledger-row">
          <div class="row-main">
            <span class="row-id">new</span>
            <input
              v-model="newCustomerDraft.first_name"
              type="text"
              class="field"
              placeholder="First name"
            />
            <input
              v-model="newCustomerDraft.last_name"
              type="text"
              class="field"
              placeholder="Last name"
            />
            <select v-model="newCustomerDraft.active" class="field">
              <option :value="true">true</option>
              <option :value="false">false</option>
            </select>
            <span class="row-actions">
              <LinkButton :disabled="savingNewCustomer" @click="createCustomer">
                {{ savingNewCustomer ? "Saving..." : "Save" }}
              </LinkButton>
              <LinkButton :disabled="savingNewCustomer" @click="cancelCreate">
                Cancel
              </LinkButton>
            </span>
          </div>
          <div class="detail-line">
            <span class="detail-field">
              <span class="field-label">Email</span>
              <input v-model="newCustomerDraft.email" type="text" class="field" placeholder="Email" />
            </span>
            <span class="detail-field">
              <span class="field-label">Phone</span>
              <input v-model="newCustomerDraft.phone" type="text" class="field" placeholder="Phone" />
            </span>
            <span class="detail-field">
              <span class="field-label">Points</span>
              <input
                v-model.number="newCustomerDraft.loyalty_points"
                type="text"
                class="field"
                placeholder="Loyalty Points"
              />
            </span>
            <span class="detail-field">
              <span class="field-label">Expires</span>
              <span>—</span>
            </span>
          </div>
        </li>
        <li v-for="row in rows" :key="row.customer.id" class="ledger-row">
          <div class="row-main">
            <span class="row-id">{{ row.customer.id }}</span>
            <template v-if="row.draft">
              <input v-model="row.draft.first_name" type="text" class="field" />
              <input v-model="row.draft.last_name" type="text" class="field" />
              <select v-model="row.draft.active" class="field">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
              <span class="row-actions">
                <LinkButton
                  :disabled="savingCustomerIds.has(row.customer.id)"
                  @click="saveEdit(row.customer.id)"
                >
                  {{ savingCustomerIds.has(row.customer.id) ? "Saving..." : "Save" }}
                </LinkButton>
                <LinkButton
                  :disabled="savingCustomerIds.has(row.customer.id)"
                  @click="cancelEdit(row.customer.id)"
                >
                  Cancel
                </LinkButton>
              </span>
            </template>
            <template v-else>
              <span>{{ row.customer.first_name }}</span>
              <span>{{ row.customer.last_name }}</span>
              <span>{{ row.customer.active }}</span>
              <span class="row-actions">
                <LinkButton @click="startEdit(row.customer)">Edit</LinkButton>
                <LinkButton
                  :disabled="deletingCustomerId === row.customer.id"
                  @click="deleteCustomer(row.customer)"
                >
                  {{ deletingCustomerId === row.customer.id ? "Deleting..." : "Delete" }}
                </LinkButton>
              </span>
            </template>
          </div>
          <div v-if="row.draft" class="detail-line">
            <span class="detail-field">
              <span class="field-label">Email</span>
              <input v-model="row.draft.email" type="text" class="field" placeholder="Email" />
            </span>
            <span class="detail-field">
              <span class="field-label">Phone</span>
              <input v-model="row.draft.phone" type="text" class="field" placeholder="Phone" />
            </span>
            <span class="detail-field">
              <span class="field-label">Points</span>
              <input
                v-model.number="row.draft.loyalty_points"
                type="text"
                class="field"
                placeholder="Loyalty Points"
              />
            </span>
            <span class="detail-field">
              <span class="field-label">Expires</span>
              <span>{{ formatDate(row.customer.loyalty_expires_at) }}</span>
            </span>
          </div>
          <div v-else class="detail-line">
            <span class="detail-field">
              <span class="field-label">Email</span>
              <span>{{ row.customer.email }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Phone</span>
              <span>{{ row.customer.phone }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Points</span>
              <span>{{ row.customer.loyalty_points }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Expires</span>
              <span>{{ formatDate(row.customer.loyalty_expires_at) }}</span>
            </span>
          </div>
        </li>
      </ul>
    </template>
  </main>
</template>
