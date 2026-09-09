<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiLogin } from "@/api/auth";
import { useSession } from "@/composables/useSession";
import FormMessage from "@/components/FormMessage.vue";

const { login } = useSession();
const router = useRouter();

const username = ref("");
const password = ref("");
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
    router.push({ name: "dashboard" });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="page">
    <section class="card">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Employee login showcase</p>
      </header>

      <h2>Log in</h2>

      <FormMessage :text="errorMessage" type="error" />

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
          <input
            id="password"
            v-model="password"
            name="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </div>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? "Please wait…" : "Log in" }}
        </button>
      </form>
    </section>
  </main>
</template>
