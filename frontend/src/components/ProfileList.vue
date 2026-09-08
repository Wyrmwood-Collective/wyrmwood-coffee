<script setup lang="ts">
import { computed } from "vue";
import type { EmployeeRead } from "@/types/employee";

const props = defineProps<{
  employee: EmployeeRead;
  limited?: boolean;
}>();

const rows = computed(() => {
  const base: [string, string | number][] = [
    ["Name", `${props.employee.first_name} ${props.employee.last_name}`],
    ["Username", props.employee.username],
    ["Role", props.employee.role],
  ];

  if (props.limited) {
    base.push(["Hire date", props.employee.hire_date]);
  } else {
    base.push(
      ["Status", props.employee.active ? "Active" : "Inactive"],
      ["Hourly rate", `$${props.employee.hourly_rate}`],
      ["Employee ID", props.employee.id],
      ["Hire date", props.employee.hire_date],
      ["Termination date", props.employee.term_date ?? "—"],
    );
  }

  return base;
});
</script>

<template>
  <ul class="profile-list">
    <li v-for="[label, value] in rows" :key="label">
      <span>{{ label }}</span>
      <strong>{{ value }}</strong>
    </li>
  </ul>
</template>
