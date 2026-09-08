<script setup lang="ts">
import { computed } from "vue";
import { useSession } from "@/composables/useSession";

const { session, can } = useSession();

const roleLabel = computed(() => {
  if (session.value?.role === "admin") return "Admin";
  if (session.value?.role === "manager") return "Manager";
  return "Employee";
});

const links = computed(() => {
  const items = [{ to: "/dashboard", label: "My profile" }];
  if (can("listEmployees")) {
    items.push({ to: "/employees", label: "Team roster" });
  }
  if (can("createEmployee")) {
    items.push({ to: "/signup", label: "Create employee" });
  }
  return items;
});
</script>

<template>
  <div class="app-bar">
    <nav class="app-nav" aria-label="Main">
      <RouterLink v-for="link in links" :key="link.to" class="nav-link" :to="link.to">
        {{ link.label }}
      </RouterLink>
    </nav>
    <span class="role-badge" :class="`role-badge-${session?.role}`">{{ roleLabel }}</span>
  </div>
</template>
