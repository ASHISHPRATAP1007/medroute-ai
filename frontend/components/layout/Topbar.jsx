"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, LogOut, Menu, Search } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { listNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead } from "@/services/notification-service";

function NotificationsMenu() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: countData } = useQuery({ queryKey: ["unread-count"], queryFn: getUnreadCount, refetchInterval: 30000 });
  const { data: listData } = useQuery({ queryKey: ["notifications"], queryFn: listNotifications, enabled: open });

  const unreadCount = countData?.data?.unread_count || 0;
  const notifications = listData?.data || [];

  const readMutation = useMutation({
    mutationFn: (id) => markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["unread-count"] });
    },
  });

  const readAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["unread-count"] });
    },
  });

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-lg p-1.5 hover:bg-slate-100"
        aria-label="Notifications"
        aria-expanded={open}
      >
        <Bell className="h-5 w-5 text-slate-500" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger-500 px-1 text-[10px] font-medium text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className="absolute right-0 z-50 mt-2 w-80 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
            <div className="flex items-center justify-between px-2 py-1">
              <span className="text-sm font-medium text-slate-900">Notifications</span>
              {unreadCount > 0 && (
                <button onClick={() => readAllMutation.mutate()} className="text-xs font-medium text-primary-600 hover:underline">
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="px-2 py-6 text-center text-sm text-slate-400">No notifications yet.</p>
              ) : (
                notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && readMutation.mutate(n.id)}
                    className={`block w-full rounded-xl px-2 py-2 text-left text-sm hover:bg-slate-50 ${!n.is_read ? "bg-primary-50/50" : ""}`}
                  >
                    <p className="font-medium text-slate-900">{n.title}</p>
                    <p className="text-xs text-slate-500">{n.message}</p>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function Topbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="rounded-lg p-1.5 hover:bg-slate-100 sm:hidden" aria-label="Open menu">
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <div className="hidden items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 sm:flex">
          <Search className="h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Search doctors, shops, stockists…"
            className="w-64 border-none bg-transparent text-sm outline-none placeholder:text-slate-400"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <NotificationsMenu />
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-slate-900">{user?.full_name}</p>
          <p className="text-xs text-slate-500">{user?.role}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
          {user?.full_name?.[0]?.toUpperCase() || "U"}
        </div>
        <button onClick={handleLogout} className="rounded-lg p-1.5 hover:bg-slate-100" aria-label="Logout">
          <LogOut className="h-5 w-5 text-slate-500" aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
