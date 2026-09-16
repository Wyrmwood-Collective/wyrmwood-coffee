import { ref, watch } from "vue";
import { client } from "@/api/client";
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

      const response = await client.GET("/employees/{id}", {
        params: { path: { id: Number(current.employeeId) } },
      });

      if (!response.data) {
        employee.value = null;
      } else {
        employee.value = response.data;
      }
    },
    { immediate: true },
  );

  return { employee };
}
