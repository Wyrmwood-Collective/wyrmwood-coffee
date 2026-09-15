<script setup lang="ts">
import { ref, onMounted } from "vue";

interface Promotion {
  id: number;
  active: boolean;
  promo_code: string;
  discount_percentage: string;
  start_date: string;
  end_date: string;
}

const promotions = ref<Promotion[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const response = await fetch("/promotions");
    promotions.value = await response.json();
  } catch (error) {
    console.log(error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped lang="scss">
/* Ledger layout, built from nested lists rather than a table — see
   VendorsView.vue for the full rationale. Each promotion is one entry
   (bordered as a whole, like a ledger account) with an indented "memo" line
   for its discount window. */
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
.promotion-main {
  display: grid;
  grid-template-columns: 3em 1fr 90px auto;
  gap: 16px;
  padding: 10px 16px;
}

.ledger-head {
  padding-bottom: 10px;
  border-bottom: 3px double var(--ink-soft, #6b5f4f);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.promotion-main {
  align-items: baseline;
}

/* closes out each promotion's block with a heavier rule, the way a ledger
   separates one account from the next */
.promotion {
  border-bottom: 2px solid var(--ink-soft, #6b5f4f);

  &:last-child {
    border-bottom: none;
  }
}

.promotion-id {
  color: var(--ink-soft, #6b5f4f);
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.detail-line {
  display: grid;
  grid-template-columns: 110px 130px 130px;
  gap: 2px 16px;
  padding: 5px 16px 5px 40px;
  font-size: 0.94em;
  color: var(--ink-soft, #6b5f4f);
}
</style>

<template>
  <main class="page">
    <h1>Promotions</h1>
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-head">
        <span class="promotion-id">ID</span>
        <span>Promo Code</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li
          v-for="promotion in promotions"
          :key="promotion.id"
          class="promotion"
        >
          <div class="promotion-main">
            <span class="promotion-id">{{ promotion.id }}</span>
            <span>{{ promotion.promo_code }}</span>
            <span>{{ promotion.active }}</span>
            <span></span>
          </div>
          <div class="detail-line">
            <span>{{ promotion.discount_percentage }}% off</span>
            <span>from {{ promotion.start_date }}</span>
            <span>to {{ promotion.end_date }}</span>
          </div>
        </li>
      </ul>
    </template>
  </main>
</template>
