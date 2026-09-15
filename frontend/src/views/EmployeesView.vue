<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { client, authHeaders, extractErrorDetail } from "@/api/client";
import { useSession } from "@/composables/useSession";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { components } from "@/types/api";

type Employee = components["schemas"]["EmployeeRead"];
type EmployeeRole = components["schemas"]["EmployeeRole"];

const router = useRouter();
const { can } = useSession();

const employees = ref<Employee[]>([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const { data, error } = await client.GET("/employees");
  if (error) {
    errorMessage.value = "Could not load employees.";
  } else {
    employees.value = data;
  }
  loading.value = false;
});

// represents an employee being in-place edited
interface EmployeeDraft {
  active: boolean;
  first_name: string;
  last_name: string;
  role: EmployeeRole;
  hourly_rate: string;
  hire_date: string;
  term_date: string | null;
  username: string;
}

const drafts = ref<Record<number, EmployeeDraft>>({});
const savingEmployeeIds = ref<Set<number>>(new Set());
const deletingEmployeeId = ref<number | null>(null);

// the actual rendered values (saved or draft)
const rows = computed(() =>
  employees.value.map((employee) => ({
    employee,
    draft: drafts.value[employee.id],
  })),
);

function startEdit(employee: Employee) {
  drafts.value[employee.id] = {
    active: employee.active,
    first_name: employee.first_name,
    last_name: employee.last_name,
    role: employee.role,
    hourly_rate: employee.hourly_rate,
    hire_date: employee.hire_date,
    term_date: employee.term_date ?? null,
    username: employee.username,
  };
}

function cancelEdit(employeeId: number) {
  delete drafts.value[employeeId];
}

async function saveEdit(employeeId: number) {
  const draft = drafts.value[employeeId];
  if (!draft) {
    return;
  }

  savingEmployeeIds.value.add(employeeId);
  errorMessage.value = "";

  const { data, error } = await client.PUT("/employees/{id}", {
    params: { path: { id: employeeId } },
    headers: authHeaders(),
    body: draft,
  });

  savingEmployeeIds.value.delete(employeeId);

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not save employee.");
    return;
  }

  const index = employees.value.findIndex((employee) => employee.id === data.id);
  employees.value[index] = data;
  cancelEdit(employeeId);
}

async function deleteEmployee(employee: Employee) {
  errorMessage.value = "";
  deletingEmployeeId.value = employee.id;

  const { error } = await client.DELETE("/employees/{id}", {
    params: { path: { id: employee.id } },
    headers: authHeaders(),
  });

  deletingEmployeeId.value = null;

  if (error) {
    errorMessage.value = extractErrorDetail(error, "Could not delete employee.");
    return;
  }

  employees.value = employees.value.filter((e) => e.id !== employee.id);
  cancelEdit(employee.id);
}

// Employee creation collects a password and lives on its own page (with
// confirmation + strength validation) rather than as an inline ledger row.
function goToCreateEmployee() {
  router.push({ name: "signup" });
}
</script>

<style scoped>
/* Ledger layout — see VendorsView.vue for the full rationale. Shared
   ledger styling lives in the main stylesheet; only this page's column
   widths stay here. */
.page {
  display: block;
  color: var(--ink);
}

.ledger-head,
.row-main {
  grid-template-columns: 3em 1fr 1fr 110px 90px 170px;
}

.detail-line {
  grid-template-columns: 110px 130px 130px 1fr;
}

.detail-field {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
}

.field-label {
  flex: 0 0 auto;
  font-size: 0.78em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--ink-soft);
}

.detail-field .field {
  flex: 1 1 auto;
  min-width: 0;
}
</style>

<template>
  <main class="page">
    <h1>Employees</h1>
    <FormMessage :text="errorMessage" type="error" />
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div v-if="can('createEmployee')" class="ledger-toolbar">
        <LinkButton @click="goToCreateEmployee">New employee</LinkButton>
      </div>
      <div class="ledger-head">
        <span class="row-id">ID</span>
        <span>First Name</span>
        <span>Last Name</span>
        <span>Role</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li v-for="row in rows" :key="row.employee.id" class="ledger-row">
          <div class="row-main">
            <span class="row-id">{{ row.employee.id }}</span>
            <template v-if="row.draft">
              <input v-model="row.draft.first_name" type="text" class="field" />
              <input v-model="row.draft.last_name" type="text" class="field" />
              <select v-model="row.draft.role" class="field">
                <option value="employee">employee</option>
                <option value="manager">manager</option>
                <option value="admin">admin</option>
              </select>
              <select v-model="row.draft.active" class="field">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
              <span class="row-actions">
                <LinkButton
                  :disabled="savingEmployeeIds.has(row.employee.id)"
                  @click="saveEdit(row.employee.id)"
                >
                  {{ savingEmployeeIds.has(row.employee.id) ? "Saving..." : "Save" }}
                </LinkButton>
                <LinkButton
                  :disabled="savingEmployeeIds.has(row.employee.id)"
                  @click="cancelEdit(row.employee.id)"
                >
                  Cancel
                </LinkButton>
              </span>
            </template>
            <template v-else>
              <span>{{ row.employee.first_name }}</span>
              <span>{{ row.employee.last_name }}</span>
              <span>{{ row.employee.role }}</span>
              <span>{{ row.employee.active }}</span>
              <span class="row-actions">
                <LinkButton v-if="can('updateEmployee')" @click="startEdit(row.employee)">
                  Edit
                </LinkButton>
                <LinkButton
                  v-if="can('deleteEmployee')"
                  :disabled="deletingEmployeeId === row.employee.id"
                  @click="deleteEmployee(row.employee)"
                >
                  {{ deletingEmployeeId === row.employee.id ? "Deleting..." : "Delete" }}
                </LinkButton>
              </span>
            </template>
          </div>
          <div v-if="row.draft" class="detail-line">
            <span class="detail-field">
              <span class="field-label">Rate</span>
              <input
                v-if="can('viewHourlyRate')"
                v-model="row.draft.hourly_rate"
                type="text"
                class="field"
                placeholder="Hourly Rate"
              />
            </span>
            <span class="detail-field">
              <span class="field-label">Hired</span>
              <input v-model="row.draft.hire_date" type="date" class="field" />
            </span>
            <span class="detail-field">
              <span class="field-label">Term</span>
              <input v-model="row.draft.term_date" type="date" class="field" />
            </span>
            <span class="detail-field">
              <span class="field-label">Username</span>
              <input v-model="row.draft.username" type="text" class="field" placeholder="Username" />
            </span>
          </div>
          <div v-else class="detail-line">
            <span class="detail-field">
              <span class="field-label">Rate</span>
              <span>{{ can("viewHourlyRate") ? `$${row.employee.hourly_rate}/hr` : "—" }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Hired</span>
              <span>{{ row.employee.hire_date }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Term</span>
              <span>{{ row.employee.term_date ?? "—" }}</span>
            </span>
            <span class="detail-field">
              <span class="field-label">Username</span>
              <span>{{ row.employee.username }}</span>
            </span>
          </div>
        </li>
      </ul>
    </template>
  </main>
</template>
