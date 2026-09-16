<script setup lang="ts">
import { ref } from "vue";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";

const phoneNumber = ref("");
const hasSearched = ref(false);
const searchError = ref("");
const isLoading = ref(false);

const customer = ref<{
  firstName: string;
  lastName: string;
  phone: string;
} | null>(null);

const favoriteDrink = ref({
  name: null as string | null,
  quantity: 0,
  isFavorite: false,
});

const favoriteBakedGood = ref({
  name: null as string | null,
  quantity: 0,
  isFavorite: false,
});

async function searchCustomer() {
  searchError.value = "";
  hasSearched.value = false;
  customer.value = null;
  isLoading.value = true;

  try {
    const response = await fetch(
      `/customers/favorites?phone=${encodeURIComponent(phoneNumber.value)}`,
    );

    if (response.status === 404) {
      searchError.value = "Phone number not found.";
      return;
    }

    if (!response.ok) {
      searchError.value = "Unable to search for customer favorites.";
      return;
    }

    const data = await response.json();

    customer.value = {
      firstName: data.customer.first_name,
      lastName: data.customer.last_name,
      phone: data.customer.phone,
    };

    favoriteDrink.value = {
      name: data.drink.name,
      quantity: data.drink.quantity,
      isFavorite: data.drink.is_favorite,
    };

    favoriteBakedGood.value = {
      name: data.baked_good.name,
      quantity: data.baked_good.quantity,
      isFavorite: data.baked_good.is_favorite,
    };

    hasSearched.value = true;
  } catch {
    searchError.value = "Unable to search for customer favorites.";
  } finally {
    isLoading.value = false;
  }
}

function formatPhoneNumber() {
  const digits = phoneNumber.value.replace(/\D/g, "").slice(0, 10);

  if (digits.length <= 3) {
    phoneNumber.value = digits;
  } else if (digits.length <= 6) {
    phoneNumber.value = `${digits.slice(0, 3)}-${digits.slice(3)}`;
  } else {
    phoneNumber.value = `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
}

function clearSearch() {
  phoneNumber.value = "";
  hasSearched.value = false;
  searchError.value = "";
  customer.value = null;

  favoriteDrink.value = {
    name: null,
    quantity: 0,
    isFavorite: false,
  };

  favoriteBakedGood.value = {
    name: null,
    quantity: 0,
    isFavorite: false,
  };
}
</script>

<style scoped>
.page {
  display: block;
  color: var(--ink);
}

.hint {
  max-width: 46em;
}

.favorites-search {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem 0.5rem;
  margin: 1.25rem 0;
}

.favorites-search .form-field {
  flex: 1 1 220px;
  margin: 0;
  max-width: 280px;
}

.input-clear {
  position: relative;
}

.input-clear input {
  padding-right: 2.25rem;
}

.input-clear-btn {
  position: absolute;
  top: 50%;
  right: 6px;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  line-height: 1;
  color: var(--ink-soft);
  cursor: pointer;
}

.input-clear-btn:hover {
  color: var(--ink);
}

.favorites-actions {
  display: flex;
  align-items: center;
  /* Offsets the button's text baseline to match the phone input's: the
     input's own text sits above its box's bottom edge by its vertical
     padding (0.65rem) plus its 1px border, so this reproduces that same
     inset on the button's otherwise unpadded box. */
  padding-bottom: calc(0.65rem + 1px);
}

.favorites-customer {
  margin: 1.25rem 0;
}

.favorites-customer h2 {
  margin-bottom: 0.75rem;
}

.favorites-section {
  margin-top: 1.75rem;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
  margin-top: 1rem;
}

.favorite-card {
  padding: 1rem 1.25rem;
  border: 1px solid rgba(43, 36, 32, 0.3);
  border-radius: 2px;
  background: rgba(255, 248, 228, 0.45);
}

.favorite-card h3 {
  margin: 0.35rem 0 0.75rem;
  font-family: "MedievalSharp", Georgia, serif;
  font-weight: 400;
  font-size: 1.1rem;
  color: var(--ink);
}

.favorite-type {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.favorite-count {
  margin: 0;
  color: var(--ink-soft);
}

.favorite-count strong {
  color: var(--ink);
}

.favorite-progress {
  margin-top: 0.6rem;
  height: 8px;
  border: 1px solid rgba(43, 36, 32, 0.3);
  border-radius: 2px;
  background: rgba(43, 36, 32, 0.08);
  overflow: hidden;
}

.favorite-progress-fill {
  height: 100%;
  background: var(--leather);
}

.favorites-note {
  margin-top: 1.25rem;
}

@media (max-width: 600px) {
  .favorites-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <main class="page">
    <h1>Customer Favorites</h1>

    <p class="hint">
      Search for an active customer by phone number to view their favorite items.
    </p>

    <form class="favorites-search" @submit.prevent="searchCustomer">
      <div class="form-field">
        <label for="customer-phone">Phone number</label>

        <div class="input-clear">
          <input
            id="customer-phone"
            v-model="phoneNumber"
            type="tel"
            placeholder="xxx-xxx-xxxx"
            inputmode="numeric"
            maxlength="12"
            pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}"
            title="Enter a 10-digit phone number"
            required
            @input="formatPhoneNumber"
          />
          <button
            v-if="phoneNumber || hasSearched || searchError"
            type="button"
            class="input-clear-btn"
            aria-label="Clear search"
            @click="clearSearch"
          >
            ×
          </button>
        </div>
      </div>

      <div class="favorites-actions">
        <LinkButton type="submit" :disabled="isLoading">
          {{ isLoading ? "Searching..." : "Search Customer" }}
        </LinkButton>
      </div>
    </form>

    <FormMessage :text="searchError" type="error" />

    <section v-if="hasSearched && customer" class="favorites-customer">
      <h2>Customer</h2>

      <ul class="profile-list">
        <li>
          <span>Name</span>
          <strong> {{ customer.firstName }} {{ customer.lastName }} </strong>
        </li>

        <li>
          <span>Phone</span>
          <strong>{{ customer.phone }}</strong>
        </li>
      </ul>
    </section>

    <section v-if="hasSearched && customer" class="favorites-section">
      <h2>Favorite Items</h2>

      <div class="favorites-grid">
        <article class="favorite-card">
          <p class="favorite-type">Favorite Drink</p>

          <template v-if="favoriteDrink.isFavorite">
            <h3>{{ favoriteDrink.name }}</h3>

            <p class="favorite-count">
              Total purchased:
              <strong>{{ favoriteDrink.quantity }}</strong>
            </p>
          </template>

          <template v-else>
            <h3>No favorite yet</h3>

            <p class="favorite-count">{{ favoriteDrink.quantity }} of 5 purchases</p>

            <div class="favorite-progress">
              <div
                class="favorite-progress-fill"
                :style="{
                  width: `${Math.min((favoriteDrink.quantity / 5) * 100, 100)}%`,
                }"
              ></div>
            </div>
          </template>
        </article>

        <article class="favorite-card">
          <p class="favorite-type">Favorite Baked Good</p>

          <template v-if="favoriteBakedGood.isFavorite">
            <h3>{{ favoriteBakedGood.name }}</h3>

            <p class="favorite-count">
              Total purchased:
              <strong>{{ favoriteBakedGood.quantity }}</strong>
            </p>
          </template>

          <template v-else>
            <h3>No favorite yet</h3>

            <p class="favorite-count">{{ favoriteBakedGood.quantity }} of 5 purchases</p>

            <div class="favorite-progress">
              <div
                class="favorite-progress-fill"
                :style="{
                  width: `${Math.min((favoriteBakedGood.quantity / 5) * 100, 100)}%`,
                }"
              ></div>
            </div>
          </template>
        </article>
      </div>

      <p class="hint favorites-note">
        Favorites are based on completed customer orders and do not include guest orders. 5
        purchases unlocks a customer favorite.
      </p>
    </section>
  </main>
</template>
