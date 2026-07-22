"use server";

import { revalidatePath } from "next/cache";

import type { CandidateProfile } from "@career-os/sdk";

import { createCareerOsServerClient } from "@/lib/api";

function refresh() {
  revalidatePath("/app");
  revalidatePath("/app/profile");
  revalidatePath("/app/notifications");
}

export async function saveProfilePreferencesAction(
  body: Parameters<Awaited<ReturnType<typeof createCareerOsServerClient>>["upsertProfile"]>[0],
): Promise<CandidateProfile> {
  const api = await createCareerOsServerClient();
  const profile = await api.upsertProfile(body);
  refresh();
  return profile;
}

export async function ingestResumeAction(text: string): Promise<CandidateProfile> {
  const api = await createCareerOsServerClient();
  const profile = await api.ingestResume(text);
  refresh();
  return profile;
}

export async function ingestLinkedInAction(text: string): Promise<CandidateProfile> {
  const api = await createCareerOsServerClient();
  const profile = await api.ingestLinkedIn(text);
  refresh();
  return profile;
}

export async function enrichGitHubAction(username: string): Promise<CandidateProfile> {
  const api = await createCareerOsServerClient();
  const profile = await api.enrichGitHub(username);
  refresh();
  return profile;
}

export async function enrichPortfolioAction(url: string): Promise<CandidateProfile> {
  const api = await createCareerOsServerClient();
  const profile = await api.enrichPortfolio(url);
  refresh();
  return profile;
}
