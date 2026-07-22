import Link from "next/link";
import { notFound } from "next/navigation";

import { CareerOsApiError } from "@career-os/sdk";

import { CopilotPanel } from "@/features/copilot/copilot-panel";
import { OpportunityActions } from "@/features/jobs/components/opportunity-actions";
import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const api = await createCareerOsServerClient();

  try {
    const [opportunity, copilot] = await Promise.all([
      api.getOpportunity(id),
      api.getCopilot(id),
    ]);

    return (
      <main className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex flex-col gap-6">
          <div>
            <Link href="/app" className="text-sm underline">
              Back to feed
            </Link>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">{opportunity.title}</h1>
            <p className="mt-2 text-neutral-700">
              {opportunity.company}
              {opportunity.location ? ` · ${opportunity.location}` : ""}
              {opportunity.is_remote ? " · Remote" : ""}
              {` · ${opportunity.source_kind}`}
            </p>
            {opportunity.match_score != null ? (
              <p className="mt-2 text-sm text-neutral-600">
                Match {(opportunity.match_score * 100).toFixed(0)}%
              </p>
            ) : null}
          </div>

          <OpportunityActions
            opportunityId={opportunity.id}
            applyUrl={opportunity.apply_url}
            applicationStatus={opportunity.application_status}
          />

          <section>
            <h2 className="text-lg font-medium">Role overview</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-neutral-700">
              {opportunity.description_text.slice(0, 6000)}
              {opportunity.description_text.length > 6000 ? "…" : ""}
            </p>
          </section>

          {opportunity.skills.length > 0 ? (
            <section>
              <h2 className="text-lg font-medium">Detected skills</h2>
              <p className="mt-2 text-sm text-neutral-700">{opportunity.skills.slice(0, 24).join(", ")}</p>
            </section>
          ) : null}
        </div>
        <CopilotPanel advice={copilot} />
      </main>
    );
  } catch (error) {
    if (error instanceof CareerOsApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
