"use client";

import { useRouter } from "next/navigation";

import type { AppNotification } from "@career-os/sdk";

import { markNotificationReadAction } from "@/features/intelligence/notification-actions";

export function NotificationList({ items }: { items: AppNotification[] }) {
  const router = useRouter();

  if (items.length === 0) {
    return (
      <p className="text-sm text-neutral-600">
        No notifications yet. The Job Hunter agent will notify you about strong matches and daily
        digests after the next worker cycle.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-neutral-200 border-t border-neutral-200">
      {items.map((item) => (
        <li key={item.id} className="space-y-2 py-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-medium">{item.title}</h2>
            <span className="text-xs uppercase tracking-wide text-neutral-500">
              {item.kind} · {item.status}
            </span>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-sm text-neutral-700">{item.body}</pre>
          {item.status !== "read" ? (
            <button
              type="button"
              className="text-sm underline"
              onClick={() => {
                void markNotificationReadAction(item.id).then(() => router.refresh());
              }}
            >
              Mark read
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
