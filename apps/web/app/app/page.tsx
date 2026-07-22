import Link from "next/link";

import { CareerOsApiError, type Recommendation } from "@career-os/sdk";

import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AppHomePage() {
  const api = await createCareerOsServerClient();
  let recommendations: Recommendation[] = [];
  let loadError: string | null = null;

  try {
    await api.me();
    const feed = await api.recommendations(40);
    recommendations = feed.items;
  } catch (error) {
    loadError =
      error instanceof CareerOsApiError
        ? `API ${error.status}: could not load feed`
        : error instanceof Error
          ? error.message
          : "Could not load feed";
  }

  return (
    <main className="flex flex-col gap-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Your opportunity feed</h1>
          <p className="mt-2 max-w-xl text-sm text-neutral-600">
            Highly relevant openings ranked from your profile. Open any role for Copilot
            guidance, save it, or track an application.
          </p>
        </div>
        <Link
          href="/app/profile"
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
        >
          Edit ranking profile
        </Link>
      </div>

      {loadError ? (
        <p className="text-sm text-red-700" role="alert">
          {loadError}
        </p>
      ) : null}

      {recommendations.length === 0 && !loadError ? (
        <div className="rounded border border-dashed border-neutral-300 p-6 text-sm text-neutral-600">
          No high-fit roles yet.{" "}
          <Link href="/app/profile" className="underline">
            Save your skills and preferences
          </Link>
          , wait for ingest, or{" "}
          <Link href="/app/search" className="underline">
            browse all openings
          </Link>
          .
        </div>
      ) : (
        <ul className="divide-y divide-neutral-200 border-t border-neutral-200">
          {recommendations.map((item) => (
            <li key={item.opportunity_id} className="py-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <Link
                  href={`/app/opportunities/${item.opportunity_id}`}
                  className="text-lg font-medium underline-offset-2 hover:underline"
                >
                  {item.title}
                </Link>
                <span className="text-sm tabular-nums text-neutral-600">
                  {(item.score * 100).toFixed(0)}% fit
                </span>
              </div>
              <p className="mt-1 text-sm text-neutral-700">
                {item.company}
                {item.location ? ` · ${item.location}` : ""}
                {item.is_remote ? " · Remote" : ""}
              </p>
              {item.reasons[0] ? (
                <p className="mt-2 text-sm text-neutral-600">{item.reasons[0]}</p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
