<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { client } from "@/api/client";
import { useSession } from "@/composables/useSession";
import FormMessage from "@/components/FormMessage.vue";
import ProfileList from "@/components/ProfileList.vue";
import type { EmployeeRead } from "@/types/employee";

const { session } = useSession();

const employee = ref<EmployeeRead | null>(null);
const errorMessage = ref("");

const accessNotes: Record<string, string> = {
  employee: "You can view your own profile only.",
  manager: "You can view the team roster. Creating or removing employees requires an admin.",
  admin: "You have full employee management access in this demo UI.",
};

const accessNote = computed(() => (session.value ? (accessNotes[session.value.role] ?? "") : ""));
const welcomeText = computed(() =>
  employee.value ? `Welcome, ${employee.value.first_name}!` : "Welcome back!",
);
const limited = computed(() => session.value?.role === "employee");

onMounted(async () => {
  if (!session.value) {
    return;
  }
  try {
    const response = await client.GET("/employees/{id}", {
      params: { path: { id: Number(session.value.employeeId) } },
    });
    if (!response.data) {
      throw new Error("Could not load employee.");
    }
    employee.value = response.data;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  }
});
</script>

<style scoped>
.page {
  display: block;
  color: var(--ink);
}
</style>

<template>
  <main class="page">
    <h1>Dashboard</h1>

    <h2>{{ welcomeText }}</h2>
    <p class="hint access-note">{{ accessNote }}</p>

    <FormMessage :text="errorMessage" type="error" />

    <ProfileList v-if="employee" :employee="employee" :limited="limited" />
  </main>
</template>
