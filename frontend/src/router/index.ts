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
      path: "/orders",
      name: "orders",
      component: () => import("@/views/CustomerOrdersView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/employees",
      name: "employees",
      component: () => import("@/views/EmployeesView.vue"),
      meta: { requiresAuth: true, permission: "listEmployees" },
    },
    {
      path: "/customer-favorites",
      name: "customer-favorites",
      component: () => import("@/views/CustomerFavoritesView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/customers",
      name: "customers",
      component: () => import("@/views/CustomersView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/ingredients",
      name: "ingredients",
      component: () => import("@/views/IngredientsView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/promotions",
      name: "promotions",
      component: () => import("@/views/PromotionsView.vue"),
      meta: { requiresAuth: true },
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
