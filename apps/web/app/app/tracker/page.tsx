import { CareerOsApiError, type Application } from "@career-os/sdk";

import { TrackerList } from "@/features/jobs/components/tracker-list";
import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TrackerPage() {
  const api = await createCareerOsServerClient();
  let error: string | null = null;
  let items: Application[] = [];
  try {
    const result = await api.listApplications();
    items = result.items;
  } catch (err) {
    error =
      err instanceof CareerOsApiError
        ? `API ${err.status}`
        : err instanceof Error
          ? err.message
          : "Could not load tracker";
  }

  return (
    <main className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Application tracker</h1>
        <p className="mt-2 text-sm text-neutral-600">
          Track saved roles and confirmed applications. CareerOS never auto-submits.
        </p>
      </div>
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : (
        <TrackerList items={items} />
      )}
    </main>
  );
}
