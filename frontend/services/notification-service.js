import { apiRequest } from "@/lib/api-client";

export async function listNotifications() {
  return apiRequest("/notifications");
}

export async function getUnreadCount() {
  return apiRequest("/notifications/unread-count");
}

export async function markNotificationRead(id) {
  return apiRequest(`/notifications/${id}/read`, { method: "POST" });
}

export async function markAllNotificationsRead() {
  return apiRequest("/notifications/read-all", { method: "POST" });
}
