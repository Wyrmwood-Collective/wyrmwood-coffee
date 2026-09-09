<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { apiListEmployees } from "@/api/employees";
import { useSession } from "@/composables/useSession";
import AppChrome from "@/components/AppChrome.vue";
import LogoutButton from "@/components/LogoutButton.vue";
import FormMessage from "@/components/FormMessage.vue";
import EmployeeTable from "@/components/EmployeeTable.vue";
import type { EmployeeRead } from "@/types/employee";

const { session, can } = useSession();

const employees = ref<EmployeeRead[]>([]);
const errorMessage = ref("");
const successMessage = ref("");

const showRate = computed(() => can("viewHourlyRate"));
const rosterNote = computed(() =>
  session.value?.role === "admin"
    ? "Admins can create and delete employees (delete requires a future API endpoint)."
    : "Managers can browse the roster but cannot create or remove employees.",
);

function handleDeleted(id: number) {
  const removed = employees.value.find((employee) => employee.id === id);
  employees.value = employees.value.filter((employee) => employee.id !== id);
  successMessage.value = removed
    ? `${removed.first_name} ${removed.last_name} was deleted.`
    : "Employee was deleted.";
  errorMessage.value = "";
}

function handleError(message: string) {
  errorMessage.value = message;
  successMessage.value = "";
}

onMounted(async () => {
  try {
    employees.value = await apiListEmployees();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  }
});
</script>

<template>
  <main class="page">
    <section class="card card-full">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Team roster</p>
      </header>

      <AppChrome />

      <div class="section-header">
        <h2>Employees</h2>
        <RouterLink v-if="can('createEmployee')" class="btn btn-primary btn-inline" to="/signup">
          Create employee
        </RouterLink>
      </div>

      <p class="hint">{{ rosterNote }}</p>

      <FormMessage :text="errorMessage" type="error" />
      <FormMessage :text="successMessage" type="success" />

      <EmployeeTable
        :employees="employees"
        :show-rate="showRate"
        @deleted="handleDeleted"
        @error="handleError"
      />

      <LogoutButton />
    </section>
  </main>
</template>
