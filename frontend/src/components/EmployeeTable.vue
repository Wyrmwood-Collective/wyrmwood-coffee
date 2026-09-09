<script setup lang="ts">
import { ref } from "vue";
import { apiDeleteEmployee } from "@/api/employees";
import { useSession } from "@/composables/useSession";
import ProfileList from "@/components/ProfileList.vue";
import type { EmployeeRead } from "@/types/employee";

const props = defineProps<{
  employees: EmployeeRead[];
  showRate: boolean;
}>();

const emit = defineEmits<{
  deleted: [id: number];
  error: [message: string];
}>();

const { can } = useSession();

const selected = ref<EmployeeRead | null>(null);
const deleting = ref(false);

function viewEmployee(employee: EmployeeRead) {
  selected.value = employee;
}

async function deleteSelected() {
  if (!selected.value) {
    return;
  }
  const employee = selected.value;
  const name = `${employee.first_name} ${employee.last_name}`;
  if (!window.confirm(`Delete ${name}? This cannot be undone.`)) {
    return;
  }

  deleting.value = true;
  try {
    await apiDeleteEmployee(employee.id);
    selected.value = null;
    emit("deleted", employee.id);
  } catch (error) {
    emit("error", error instanceof Error ? error.message : "Something went wrong.");
  } finally {
    deleting.value = false;
  }
}
</script>

<template>
  <div class="table-wrap">
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Username</th>
          <th>Role</th>
          <th>Status</th>
          <th v-if="showRate">Rate</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="employee in props.employees" :key="employee.id">
          <td>{{ employee.first_name }} {{ employee.last_name }}</td>
          <td>{{ employee.username }}</td>
          <td>{{ employee.role }}</td>
          <td>{{ employee.active ? "Active" : "Inactive" }}</td>
          <td v-if="showRate">${{ employee.hourly_rate }}</td>
          <td>
            <button type="button" class="btn-text" @click="viewEmployee(employee)">View</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <section v-if="selected" class="detail-panel">
    <h3>{{ selected.first_name }} {{ selected.last_name }}</h3>
    <ProfileList :employee="selected" />
    <div>
      <button
        v-if="can('deleteEmployee')"
        type="button"
        class="btn btn-danger btn-inline"
        :disabled="deleting"
        @click="deleteSelected"
      >
        Delete employee
      </button>
      <p v-if="can('updateEmployee')" class="hint">
        Update will be available when the API adds PUT /employees/{id}.
      </p>
    </div>
  </section>
</template>
