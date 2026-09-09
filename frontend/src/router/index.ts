import { createRouter, createWebHistory } from "vue-router";
import { useSession, type PermissionAction } from "@/composables/useSession";

declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    permission?: PermissionAction;
    redirectIfLoggedIn?: boolean;
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { redirectIfLoggedIn: true },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/views/DashboardView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/employees",
      name: "employees",
      component: () => import("@/views/EmployeesView.vue"),
      meta: { requiresAuth: true, permission: "listEmployees" },
    },
    {
      path: "/signup",
      name: "signup",
      component: () => import("@/views/SignupView.vue"),
      meta: { requiresAuth: true, permission: "createEmployee" },
    },
  ],
});

router.beforeEach((to) => {
  const { session, can } = useSession();

  if (to.meta.redirectIfLoggedIn && session.value) {
    return { name: "dashboard" };
  }

  if (to.meta.requiresAuth && !session.value) {
    return { name: "login" };
  }

  if (to.meta.permission && !can(to.meta.permission)) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;
