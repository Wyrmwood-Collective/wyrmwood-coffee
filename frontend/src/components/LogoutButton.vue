<script setup lang="ts">
import { useRouter } from "vue-router";
import { useSession } from "@/composables/useSession";

const { logout } = useSession();
const router = useRouter();

async function handleLogout() {
  await logout();
  router.push({ name: "login" });
}
</script>

<template>
  <button class="btn btn-secondary" type="button" @click="handleLogout">Log out</button>
</template>
