<script setup lang="ts">
import { ref, onMounted } from "vue";

interface Customer {
  id: number;
  active: boolean;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  loyalty_points: number;
  loyalty_expires_at: string;
}

const customers = ref<Customer[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const response = await fetch("/customers");
    customers.value = await response.json();
  } catch (error) {
    console.log(error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped lang="scss">
/* Ledger layout, built from nested lists rather than a table — see
   VendorsView.vue for the full rationale. Each customer is one entry
   (bordered as a whole, like a ledger account) with an indented "memo" line
   for the less central account details. */
.page {
  display: block;
  color: var(--ink, #2b2420);
}

.ledger {
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
  font-size: 80%;
}

.ledger-head,
.customer-main {
  display: grid;
  grid-template-columns: 3em 1fr 1fr 90px auto;
  gap: 16px;
  padding: 10px 16px;
}

.ledger-head {
  padding-bottom: 10px;
  border-bottom: 3px double var(--ink-soft, #6b5f4f);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.customer-main {
  align-items: baseline;
}

/* closes out each customer's block with a heavier rule, the way a ledger
   separates one account from the next */
.customer {
  border-bottom: 2px solid var(--ink-soft, #6b5f4f);

  &:last-child {
    border-bottom: none;
  }
}

.customer-id {
  color: var(--ink-soft, #6b5f4f);
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.detail-line {
  display: grid;
  grid-template-columns: 1.4fr 140px 90px 140px;
  gap: 2px 16px;
  padding: 5px 16px 5px 40px;
  font-size: 0.94em;
  color: var(--ink-soft, #6b5f4f);
}
</style>

<template>
  <main class="page">
    <h1>Customers</h1>
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-head">
        <span class="customer-id">ID</span>
        <span>First Name</span>
        <span>Last Name</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li
          v-for="customer in customers"
          :key="customer.id"
          class="customer"
        >
          <div class="customer-main">
            <span class="customer-id">{{ customer.id }}</span>
            <span>{{ customer.first_name }}</span>
            <span>{{ customer.last_name }}</span>
            <span>{{ customer.active }}</span>
            <span></span>
          </div>
          <div class="detail-line">
            <span>{{ customer.email }}</span>
            <span>{{ customer.phone }}</span>
            <span>{{ customer.loyalty_points }} pts</span>
            <span>expires {{ customer.loyalty_expires_at }}</span>
          </div>
        </li>
      </ul>
    </template>
  </main>
</template>
