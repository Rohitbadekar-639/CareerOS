import { CareerOsApiError, type CandidateProfile } from "@career-os/sdk";

import { IntelligenceProfileForm } from "@/features/intelligence/profile-form";
import { createCareerOsServerClient } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const api = await createCareerOsServerClient();
  let profile: CandidateProfile | null = null;
  let error: string | null = null;
  try {
    profile = await api.getProfile();
  } catch (err) {
    error =
      err instanceof CareerOsApiError
        ? `API ${err.status}`
        : err instanceof Error
          ? err.message
          : "Could not load profile";
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Career intelligence</h1>
        <p className="mt-2 text-sm text-neutral-600">
          Build a unified profile from resume, LinkedIn paste, GitHub, and portfolio. Matching
          and the Job Hunter agent rerank from this source of truth.
        </p>
      </div>
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : profile ? (
        <IntelligenceProfileForm initial={profile} />
      ) : null}
    </main>
  );
}
