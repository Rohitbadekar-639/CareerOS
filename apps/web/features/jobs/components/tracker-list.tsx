"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Application } from "@career-os/sdk";

import { updateApplicationStatusAction } from "@/features/jobs/actions";

const NEXT: Record<string, string[]> = {
  interested: ["prepared", "applied", "withdrawn"],
  prepared: ["applied", "withdrawn"],
  applied: ["interviewing", "rejected", "withdrawn", "offer"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["closed", "withdrawn", "rejected"],
};

export function TrackerList({ items }: { items: Application[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onStatus(id: string, status: string) {
    setError(null);
    try {
      await updateApplicationStatusAction(id, status);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-neutral-600">
        No applications yet. Save or apply from an{" "}
        <Link href="/app" className="underline">
          opportunity
        </Link>
        .
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      <ul className="divide-y divide-neutral-200 border-t border-neutral-200">
        {items.map((item) => (
          <li key={item.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <Link
                href={`/app/opportunities/${item.opportunity_id}`}
                className="font-medium underline-offset-2 hover:underline"
              >
                {item.title ?? "Opportunity"}
              </Link>
              <p className="mt-1 text-sm text-neutral-700">
                {item.company}
                {item.location ? ` · ${item.location}` : ""}
                {` · ${item.status}`}
              </p>
              {item.cover_letter_draft ? (
                <p className="mt-1 text-xs text-amber-800">Cover letter draft attached</p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {(NEXT[item.status] ?? []).map((status) => (
                <button
                  key={status}
                  type="button"
                  className="rounded border border-neutral-300 px-2 py-1 text-xs"
                  onClick={() => {
                    void onStatus(item.id, status);
                  }}
                >
                  → {status}
                </button>
              ))}
              {item.apply_url ? (
                <a
                  className="rounded border border-neutral-300 px-2 py-1 text-xs"
                  href={item.apply_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Open listing
                </a>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
