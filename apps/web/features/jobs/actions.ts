"use server";

import { revalidatePath } from "next/cache";

import { createCareerOsServerClient } from "@/lib/api";

export async function saveOpportunityAction(opportunityId: string) {
  const api = await createCareerOsServerClient();
  await api.saveOpportunity(opportunityId);
  revalidatePath(`/app/opportunities/${opportunityId}`);
  revalidatePath("/app/tracker");
}

export async function markAppliedAction(opportunityId: string) {
  const api = await createCareerOsServerClient();
  await api.markApplied(opportunityId);
  revalidatePath(`/app/opportunities/${opportunityId}`);
  revalidatePath("/app/tracker");
}

export async function generateCoverLetterAction(opportunityId: string) {
  const api = await createCareerOsServerClient();
  const draft = await api.generateCoverLetter(opportunityId);
  revalidatePath(`/app/opportunities/${opportunityId}`);
  revalidatePath("/app/tracker");
  return draft;
}

export async function updateApplicationStatusAction(applicationId: string, status: string) {
  const api = await createCareerOsServerClient();
  await api.updateApplicationStatus(applicationId, status);
  revalidatePath("/app/tracker");
}
