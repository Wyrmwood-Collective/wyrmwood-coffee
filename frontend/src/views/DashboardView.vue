<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { apiGetEmployee } from "@/api/employees";
import { useSession } from "@/composables/useSession";
import AppChrome from "@/components/AppChrome.vue";
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
    employee.value = await apiGetEmployee(session.value.employeeId);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  }
});
</script>

<template>
  <main class="page">
    <section class="card card-wide">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Employee dashboard showcase</p>
      </header>

      <AppChrome />

      <h2>{{ welcomeText }}</h2>
      <p class="hint access-note">{{ accessNote }}</p>

      <FormMessage :text="errorMessage" type="error" />

      <ProfileList v-if="employee" :employee="employee" :limited="limited" />
    </section>
  </main>
</template>
