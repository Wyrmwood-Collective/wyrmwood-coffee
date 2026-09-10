<script setup lang="ts">
import { computed } from "vue";
import { useSession } from "@/composables/useSession";

const { session } = useSession();

const roleLabel = computed(() => {
  if (session.value?.role === "admin") return "Admin";
  if (session.value?.role === "manager") return "Manager";
  return "Employee";
});
</script>

<template>
  <div class="app-bar">
    <span class="role-badge" :class="`role-badge-${session?.role}`">{{ roleLabel }}</span>
  </div>
</template>
