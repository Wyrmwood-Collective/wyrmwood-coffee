<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { client, authHeaders, extractErrorDetail } from "@/api/client";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { components } from "@/types/api";

type Ingredient = components["schemas"]["IngredientRead"];

const VALID_UNITS = [
  "g",
  "kg",
  "oz",
  "lb",
  "fl oz",
  "mL",
  "L",
  "gal",
  "pumps",
  "scoops",
  "shots",
  "dashes",
];

const ingredients = ref<Ingredient[]>([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const { data, error } = await client.GET("/ingredients");
  if (error) {
    errorMessage.value = "Could not load ingredients.";
  } else {
    ingredients.value = data;
  }
  loading.value = false;
});

// represents an ingredient being in-place edited
interface IngredientDraft {
  name: string;
  active: boolean;
  purchasing_cost: string;
  unit_amount: string;
  unit_of_measure: string;
  vendor_id: number;
  allergens: string[];
}

const drafts = ref<Record<number, IngredientDraft>>({});
const savingIngredientIds = ref<Set<number>>(new Set());
const deletingIngredientId = ref<number | null>(null);

// the actual rendered values (saved or draft)
const rows = computed(() =>
  ingredients.value.map((ingredient) => ({
    ingredient,
    draft: drafts.value[ingredient.id],
  })),
);

function startEdit(ingredient: Ingredient) {
  drafts.value[ingredient.id] = {
    name: ingredient.name,
    active: ingredient.active,
    purchasing_cost: ingredient.purchasing_cost,
    unit_amount: ingredient.unit_amount,
    unit_of_measure: ingredient.unit_of_measure,
    vendor_id: ingredient.vendor_id,
    allergens: [...(ingredient.allergens ?? [])],
  };
}

function cancelEdit(ingredientId: number) {
  delete drafts.value[ingredientId];
}

function addAllergen(ingredientId: number) {
  drafts.value[ingredientId]?.allergens.push("");
}

function removeAllergen(ingredientId: number, index: number) {
  drafts.value[ingredientId]?.allergens.splice(index, 1);
}

async function saveEdit(ingredientId: number) {
  const draft = drafts.value[ingredientId];
  if (!draft) {
    return;
  }

  savingIngredientIds.value.add(ingredientId);
  errorMessage.value = "";

  const { data, error } = await client.PUT("/ingredients/{id}", {
    params: { path: { id: ingredientId } },
    headers: authHeaders(),
    body: draft,
  });

  savingIngredientIds.value.delete(ingredientId);

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not save ingredient.");
    return;
  }

  const index = ingredients.value.findIndex((ingredient) => ingredient.id === data.id);
  ingredients.value[index] = data;
  cancelEdit(ingredientId);
}

async function deleteIngredient(ingredient: Ingredient) {
  errorMessage.value = "";
  deletingIngredientId.value = ingredient.id;

  const { error } = await client.DELETE("/ingredients/{id}", {
    params: { path: { id: ingredient.id } },
    headers: authHeaders(),
  });

  deletingIngredientId.value = null;

  if (error) {
    errorMessage.value = extractErrorDetail(error, "Could not delete ingredient.");
    return;
  }

  ingredients.value = ingredients.value.filter((i) => i.id !== ingredient.id);
  cancelEdit(ingredient.id);
}

// represents an ingredient being created
interface NewIngredientDraft {
  name: string;
  active: boolean;
  purchasing_cost: string;
  unit_amount: string;
  unit_of_measure: string;
  vendor_id: number;
  allergens: string[];
}

function emptyIngredientDraft(): NewIngredientDraft {
  return {
    name: "",
    active: true,
    purchasing_cost: "",
    unit_amount: "",
    unit_of_measure: "g",
    vendor_id: 0,
    allergens: [],
  };
}

const creatingIngredient = ref(false);
const savingNewIngredient = ref(false);
const newIngredientDraft = ref<NewIngredientDraft>(emptyIngredientDraft());

function startCreate() {
  newIngredientDraft.value = emptyIngredientDraft();
  creatingIngredient.value = true;
}

function cancelCreate() {
  creatingIngredient.value = false;
}

function addNewIngredientAllergen() {
  newIngredientDraft.value.allergens.push("");
}

function removeNewIngredientAllergen(index: number) {
  newIngredientDraft.value.allergens.splice(index, 1);
}

async function createIngredient() {
  savingNewIngredient.value = true;
  errorMessage.value = "";

  const { data, error } = await client.POST("/ingredients", {
    headers: authHeaders(),
    body: newIngredientDraft.value,
  });

  savingNewIngredient.value = false;

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not create ingredient.");
    return;
  }

  ingredients.value.push(data);
  creatingIngredient.value = false;
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
  grid-template-columns: 3em 1fr 110px 90px auto;
}

.detail-line {
  grid-template-columns: 130px 130px 1fr;
}

.sub-item-line {
  grid-template-columns: 1fr auto;
}
</style>

<template>
  <main class="page">
    <h1>Ingredients</h1>
    <FormMessage :text="errorMessage" type="error" />
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-toolbar">
        <LinkButton :disabled="creatingIngredient" @click="startCreate">
          New ingredient
        </LinkButton>
      </div>
      <div class="ledger-head">
        <span class="row-id">ID</span>
        <span>Name</span>
        <span>Vendor ID</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li v-if="creatingIngredient" class="ledger-row">
          <div class="row-main">
            <span class="row-id">new</span>
            <input
              v-model="newIngredientDraft.name"
              type="text"
              class="field"
              placeholder="Ingredient name"
            />
            <input
              v-model.number="newIngredientDraft.vendor_id"
              type="text"
              class="field"
              placeholder="Vendor ID"
            />
            <select v-model="newIngredientDraft.active" class="field">
              <option :value="true">true</option>
              <option :value="false">false</option>
            </select>
            <span class="row-actions">
              <LinkButton :disabled="savingNewIngredient" @click="createIngredient">
                {{ savingNewIngredient ? "Saving..." : "Save" }}
              </LinkButton>
              <LinkButton :disabled="savingNewIngredient" @click="cancelCreate">
                Cancel
              </LinkButton>
            </span>
          </div>
          <div class="detail-line">
            <input
              v-model="newIngredientDraft.purchasing_cost"
              type="text"
              class="field"
              placeholder="Purchasing Cost"
            />
            <input
              v-model="newIngredientDraft.unit_amount"
              type="text"
              class="field"
              placeholder="Unit Amount"
            />
            <select v-model="newIngredientDraft.unit_of_measure" class="field">
              <option v-for="unit in VALID_UNITS" :key="unit" :value="unit">{{ unit }}</option>
            </select>
          </div>
          <ul class="sub-list">
            <li v-if="!newIngredientDraft.allergens.length" class="no-sub-items">
              No allergens on file
            </li>
            <li
              v-for="(_allergen, i) in newIngredientDraft.allergens"
              :key="i"
              class="sub-item-line"
            >
              <input v-model="newIngredientDraft.allergens[i]" type="text" class="field" />
              <LinkButton @click="removeNewIngredientAllergen(i)">Remove</LinkButton>
            </li>
            <li class="sub-item-actions">
              <LinkButton @click="addNewIngredientAllergen">Add allergen</LinkButton>
            </li>
          </ul>
        </li>
        <li v-for="row in rows" :key="row.ingredient.id" class="ledger-row">
          <div class="row-main">
            <span class="row-id">{{ row.ingredient.id }}</span>
            <template v-if="row.draft">
              <input v-model="row.draft.name" type="text" class="field" placeholder="Ingredient name" />
              <input v-model.number="row.draft.vendor_id" type="text" class="field" placeholder="Vendor ID" />
              <select v-model="row.draft.active" class="field">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
              <span class="row-actions">
                <LinkButton
                  :disabled="savingIngredientIds.has(row.ingredient.id)"
                  @click="saveEdit(row.ingredient.id)"
                >
                  {{ savingIngredientIds.has(row.ingredient.id) ? "Saving..." : "Save" }}
                </LinkButton>
                <LinkButton
                  :disabled="savingIngredientIds.has(row.ingredient.id)"
                  @click="cancelEdit(row.ingredient.id)"
                >
                  Cancel
                </LinkButton>
              </span>
            </template>
            <template v-else>
              <span>{{ row.ingredient.name }}</span>
              <span>{{ row.ingredient.vendor_id }}</span>
              <span>{{ row.ingredient.active }}</span>
              <span class="row-actions">
                <LinkButton @click="startEdit(row.ingredient)">Edit</LinkButton>
                <LinkButton
                  :disabled="deletingIngredientId === row.ingredient.id"
                  @click="deleteIngredient(row.ingredient)"
                >
                  {{ deletingIngredientId === row.ingredient.id ? "Deleting..." : "Delete" }}
                </LinkButton>
              </span>
            </template>
          </div>
          <div v-if="row.draft" class="detail-line">
            <input
              v-model="row.draft.purchasing_cost"
              type="text"
              class="field"
              placeholder="Purchasing Cost"
            />
            <input v-model="row.draft.unit_amount" type="text" class="field" placeholder="Unit Amount" />
            <select v-model="row.draft.unit_of_measure" class="field">
              <option v-for="unit in VALID_UNITS" :key="unit" :value="unit">{{ unit }}</option>
            </select>
          </div>
          <div v-else class="detail-line">
            <span>${{ row.ingredient.purchasing_cost }}</span>
            <span>{{ row.ingredient.unit_amount }} {{ row.ingredient.unit_of_measure }} / unit</span>
            <span></span>
          </div>
          <ul v-if="row.draft" class="sub-list">
            <li v-if="!row.draft.allergens.length" class="no-sub-items">No allergens on file</li>
            <li v-for="(_allergen, i) in row.draft.allergens" :key="i" class="sub-item-line">
              <input v-model="row.draft.allergens[i]" type="text" class="field" />
              <LinkButton @click="removeAllergen(row.ingredient.id, i)">Remove</LinkButton>
            </li>
            <li class="sub-item-actions">
              <LinkButton @click="addAllergen(row.ingredient.id)">Add allergen</LinkButton>
            </li>
          </ul>
          <ul v-else class="sub-list">
            <li v-if="!row.ingredient.allergens?.length" class="no-sub-items">
              No allergens on file
            </li>
            <li v-for="allergen in row.ingredient.allergens" :key="allergen" class="sub-item-line">
              <span>{{ allergen }}</span>
            </li>
          </ul>
        </li>
      </ul>
    </template>
  </main>
</template>
