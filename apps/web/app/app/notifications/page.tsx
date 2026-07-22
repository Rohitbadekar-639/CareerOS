import { CareerOsApiError, type AppNotification } from "@career-os/sdk";

import { NotificationList } from "@/features/intelligence/notification-list";
import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function NotificationsPage() {
  const api = await createCareerOsServerClient();
  let items: AppNotification[] = [];
  let error: string | null = null;
  try {
    items = (await api.listNotifications()).items;
  } catch (err) {
    error =
      err instanceof CareerOsApiError
        ? `API ${err.status}`
        : err instanceof Error
          ? err.message
          : "Could not load notifications";
  }

  return (
    <main className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Notifications</h1>
        <p className="mt-2 text-sm text-neutral-600">
          Strong-match alerts and daily digests from the Job Hunter agent.
        </p>
      </div>
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : (
        <NotificationList items={items} />
      )}
    </main>
  );
}
