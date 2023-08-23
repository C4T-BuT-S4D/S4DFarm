import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "flags",
    component: () => import("@/views/Flags.vue"),
  },
  {
    path: "/teams",
    name: "teams",
    component: () => import("@/views/Teams.vue"),
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
