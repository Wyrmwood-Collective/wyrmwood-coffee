<script setup lang="ts">
import { ref } from "vue";
import AppChrome from "@/components/AppChrome.vue";

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

<template>
  <main class="page">
    <section class="card card-full">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Customer favorites</p>
      </header>

      <AppChrome />

      <div class="section-header">
        <h2>Find Customer Favorites</h2>
      </div>

      <p class="hint">
        Search for an active customer by phone number to view their favorite items.
      </p>

      <form @submit.prevent="searchCustomer">
        <div class="form-field">
          <label for="customer-phone">Phone number</label>

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
        </div>

        <button class="btn btn-primary" type="submit" :disabled="isLoading">
          {{ isLoading ? "Searching..." : "Search Customer" }}
        </button>

        <button
          v-if="hasSearched || searchError"
          class="btn btn-secondary"
          type="button"
          @click="clearSearch"
        >
          Clear Search
        </button>
      </form>

      <p v-if="searchError" class="message message-error">
        {{ searchError }}
      </p>

      <div v-if="hasSearched && customer" class="detail-panel">
        <h3>Customer</h3>

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
      </div>

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
    </section>
  </main>
</template>

<style scoped>
.favorites-section {
  margin-top: 1.5rem;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.favorite-card {
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #faf7f2;
}

.favorite-card h3 {
  margin: 0.35rem 0 0.75rem;
  color: var(--color-primary);
  font-size: 1.1rem;
}

.favorite-type {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.favorite-count {
  margin: 0;
  color: var(--color-muted);
}

.favorite-count strong {
  color: var(--color-text);
}

.favorites-note {
  margin-top: 1rem;
}

@media (max-width: 600px) {
  .favorites-grid {
    grid-template-columns: 1fr;
  }
}
</style>
