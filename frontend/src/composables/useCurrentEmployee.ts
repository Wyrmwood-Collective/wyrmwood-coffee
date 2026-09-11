import { ref, watch } from "vue";
import { apiGetEmployee } from "@/api/employees";
import { useSession } from "@/composables/useSession";
import type { EmployeeRead } from "@/types/employee";

const employee = ref<EmployeeRead | null>(null);

/** The signed-in employee's own record, for display purposes (e.g. the
 * counter header's slate). Shared across callers, refetched whenever the
 * session changes. Silent on failure — this is decorative, not a page
 * that needs to surface an error message. */
export function useCurrentEmployee() {
  const { session } = useSession();

  watch(
    session,
    async (current) => {
      if (!current) {
        employee.value = null;
        return;
      }
      try {
        employee.value = await apiGetEmployee(current.employeeId);
      } catch {
        employee.value = null;
      }
    },
    { immediate: true },
  );

  return { employee };
}
