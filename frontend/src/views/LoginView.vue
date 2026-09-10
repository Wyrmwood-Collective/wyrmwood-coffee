<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiLogin } from "@/api/auth";
import { useSession } from "@/composables/useSession";
import { usePageTransition } from "@/composables/usePageTransition";
import FormMessage from "@/components/FormMessage.vue";

const { login } = useSession();
const { fireballTransition } = usePageTransition();
const router = useRouter();

const username = ref("");
const password = ref("");
const showPassword = ref(false);
const errorMessage = ref("");
const submitting = ref(false);

async function handleSubmit() {
  errorMessage.value = "";

  const trimmedUsername = username.value.trim();
  if (!trimmedUsername || !password.value) {
    errorMessage.value = "Enter both username and password.";
    return;
  }

  submitting.value = true;
  try {
    const result = await apiLogin(trimmedUsername, password.value);
    login(result.access_token);
    fireballTransition(() => router.push({ name: "dashboard" }));
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="page">
    <section class="card login-card">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Employee login showcase</p>
      </header>

      <h2>Log in</h2>

      <div class="login-message">
        <FormMessage :text="errorMessage" type="error" />
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-field">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            name="username"
            type="text"
            autocomplete="username"
            required
          />
        </div>

        <div class="form-field">
          <label for="password">Password</label>

          <div class="password-field">
            <input
              id="password"
              v-model="password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
            />

            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <svg
                v-if="!showPassword"
                aria-hidden="true"
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>

              <svg
                v-else
                aria-hidden="true"
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="m3 3 18 18" />
                <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                <path d="M9.9 4.2A10.6 10.6 0 0 1 12 4c6.5 0 10 8 10 8a17.7 17.7 0 0 1-2 3" />
                <path d="M6.6 6.6C3.6 8.7 2 12 2 12s3.5 8 10 8a9.7 9.7 0 0 0 4.4-1" />
              </svg>
            </button>
          </div>
        </div>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? "Please wait…" : "Log in" }}
        </button>
      </form>
    </section>
  </main>
</template>
