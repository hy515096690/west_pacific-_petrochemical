import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "Studio", component: () => import("@/views/Studio.vue") },
    { path: "/workflow", name: "Workflow", component: () => import("@/views/Workflow.vue") },
    { path: "/dataset", name: "Dataset", component: () => import("@/views/Dataset.vue") },
    { path: "/chat", name: "ChatWindow", component: () => import("@/views/ChatWindow.vue") },
  ],
});

export default router;
