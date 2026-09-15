<script setup lang="ts">
import { ref, onMounted } from "vue";

interface Ingredient {
  id: number;
  active: boolean;
  name: string;
  purchasing_cost: string;
  unit_amount: string;
  unit_of_measure: string;
  vendor_id: number;
  allergens: string[];
}

const ingredients = ref<Ingredient[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const response = await fetch("/ingredients");
    ingredients.value = await response.json();
  } catch (error) {
    console.log(error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped lang="scss">
/* Ledger layout, built from nested lists rather than a table — see
   VendorsView.vue for the full rationale. Each ingredient is one entry
   (bordered as a whole, like a ledger account) containing an indented
   "memo" line of purchasing detail and an allergens list. */
.page {
  display: block;
  color: var(--ink, #2b2420);
}

.ledger,
.allergens {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ledger {
  width: 100%;
  font-size: 80%;
}

.ledger-head,
.ingredient-main {
  display: grid;
  grid-template-columns: 3em 1fr 110px 90px auto;
  gap: 16px;
  padding: 10px 16px;
}

.ledger-head {
  padding-bottom: 10px;
  border-bottom: 3px double var(--ink-soft, #6b5f4f);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.ingredient-main {
  align-items: baseline;
}

/* closes out each ingredient's block with a heavier rule, the way a ledger
   separates one account from the next */
.ingredient {
  border-bottom: 2px solid var(--ink-soft, #6b5f4f);

  &:last-child {
    border-bottom: none;
  }
}

.ingredient-id {
  color: var(--ink-soft, #6b5f4f);
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.detail-line {
  display: grid;
  grid-template-columns: 130px 130px 1fr;
  gap: 2px 16px;
  padding: 5px 16px 5px 40px;
  font-size: 0.94em;
  color: var(--ink-soft, #6b5f4f);
}

.allergen-line {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 16px;
  padding: 5px 16px 5px 40px;
  font-size: 0.94em;
  color: var(--ink-soft, #6b5f4f);

  &:not(:last-child) {
    border-bottom: 1px solid rgba(107, 95, 79, 0.18);
  }
}

.no-allergens {
  padding: 5px 16px 5px 40px;
  font-size: 0.94em;
  color: var(--ink-soft, #6b5f4f);
  font-style: italic;
}
</style>

<template>
  <main class="page">
    <h1>Ingredients</h1>
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-head">
        <span class="ingredient-id">ID</span>
        <span>Name</span>
        <span>Vendor ID</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li
          v-for="ingredient in ingredients"
          :key="ingredient.id"
          class="ingredient"
        >
          <div class="ingredient-main">
            <span class="ingredient-id">{{ ingredient.id }}</span>
            <span>{{ ingredient.name }}</span>
            <span>{{ ingredient.vendor_id }}</span>
            <span>{{ ingredient.active }}</span>
            <span></span>
          </div>
          <div class="detail-line">
            <span>${{ ingredient.purchasing_cost }}</span>
            <span>{{ ingredient.unit_amount }} {{ ingredient.unit_of_measure }} / unit</span>
            <span></span>
          </div>
          <ul class="allergens">
            <li v-if="!ingredient.allergens.length" class="no-allergens">No allergens on file</li>
            <li v-for="allergen in ingredient.allergens" :key="allergen" class="allergen-line">
              <span>{{ allergen }}</span>
            </li>
          </ul>
        </li>
      </ul>
    </template>
  </main>
</template>
