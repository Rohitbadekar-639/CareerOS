import Link from "next/link";

import { CareerOsApiError, type Opportunity } from "@career-os/sdk";

import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{
    q?: string;
    location?: string;
    remote?: string;
    company?: string;
    source?: string;
  }>;
}) {
  const params = await searchParams;
  let items: Opportunity[] = [];
  let error: string | null = null;
  try {
    const api = await createCareerOsServerClient();
    const result = await api.searchOpportunities({
      q: params.q,
      location: params.location,
      company: params.company,
      source: params.source,
      remote_only: params.remote === "1" ? true : undefined,
      limit: 50,
    });
    items = result.items;
  } catch (err) {
    error =
      err instanceof CareerOsApiError
        ? `API ${err.status}`
        : err instanceof Error
          ? err.message
          : "Search failed";
  }

  return (
    <main className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Search openings</h1>
        <p className="mt-2 text-sm text-neutral-600">
          Filter the live catalog from permitted ATS sources.
        </p>
      </div>
      <form className="grid gap-3 rounded border border-neutral-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-3" method="get">
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          name="q"
          defaultValue={params.q ?? ""}
          placeholder="Keyword"
        />
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          name="location"
          defaultValue={params.location ?? ""}
          placeholder="Location"
        />
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          name="company"
          defaultValue={params.company ?? ""}
          placeholder="Company"
        />
        <select
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          name="source"
          defaultValue={params.source ?? ""}
        >
          <option value="">Any source</option>
          <option value="greenhouse">Greenhouse</option>
          <option value="ashby">Ashby</option>
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="remote" value="1" defaultChecked={params.remote === "1"} />
          Remote only
        </label>
        <button className="rounded bg-neutral-900 px-3 py-2 text-sm text-white" type="submit">
          Apply filters
        </button>
      </form>
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      <ul className="divide-y divide-neutral-200 border-t border-neutral-200">
        {items.map((item) => (
          <li key={item.id} className="py-4">
            <Link
              href={`/app/opportunities/${item.id}`}
              className="font-medium underline-offset-2 hover:underline"
            >
              {item.title}
            </Link>
            <p className="mt-1 text-sm text-neutral-700">
              {item.company}
              {item.location ? ` · ${item.location}` : ""}
              {item.is_remote ? " · Remote" : ""}
              {` · ${item.source_kind}`}
            </p>
          </li>
        ))}
      </ul>
    </main>
  );
}
